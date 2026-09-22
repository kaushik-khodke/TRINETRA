"""
TRINETRA Phase 7 — Durable SQLite Intelligence Repository
Thread-safe, indexed, ACID-compliant persistence for investigations, findings, events, regions, monitors, and baselines.
"""

import sqlite3
import json
import threading
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from config.settings import settings
from intelligence.models import (
    CanonicalRegion,
    EOEvent,
    EventState,
    PersistentFinding,
    PersistentEvidence,
    RegionLineage,
    EventRelationship,
    InvestigationTemplate,
    MonitorDefinition,
    MonitorRun,
    MonitorAlert,
    Baseline,
    AnomalyRecord,
)


class IntelligenceRepository:
    """
    Durable storage engine for TRINETRA persistent Earth Observation intelligence.
    Supports file-based SQLite and isolated in-memory (:memory:) databases for testing.
    """

    def __init__(self, db_path: Optional[str] = None):
        raw_path = db_path or getattr(settings, "intelligence_db_path", os.path.join(settings.outputs_dir, "intelligence.db"))
        self.db_path = raw_path
        self._lock = threading.Lock()
        self._is_memory = (raw_path == ":memory:" or raw_path.startswith("file:mem"))
        if self._is_memory:
            self._uri = f"file:mem_{id(self)}?mode=memory&cache=shared"
            self._anchor_conn = sqlite3.connect(self._uri, uri=True, check_same_thread=False)
            self._anchor_conn.row_factory = sqlite3.Row
        else:
            self._anchor_conn = None
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_memory:
            conn = sqlite3.connect(self._uri, uri=True, check_same_thread=False)
        else:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()

            # 1. Investigations
            cur.execute("""
            CREATE TABLE IF NOT EXISTS investigations (
                investigation_id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                aoi_json TEXT,
                observation_ids_json TEXT,
                temporal_range_json TEXT,
                status TEXT,
                finding_ids_json TEXT,
                artifact_ids_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            """)

            # 2. Findings
            cur.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                finding_id TEXT PRIMARY KEY,
                investigation_id TEXT,
                type TEXT,
                label TEXT,
                geometry_json TEXT,
                bbox_json TEXT,
                confidence REAL,
                evidence_ids_json TEXT,
                observation_ids_json TEXT,
                metrics_json TEXT,
                semantic_class TEXT,
                fingerprint TEXT,
                model_provenance_json TEXT,
                created_at TEXT
            );
            """)

            # 3. Evidence
            cur.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                source TEXT,
                type TEXT,
                observation_id TEXT,
                geometry_json TEXT,
                bbox_json TEXT,
                value_json TEXT,
                quality REAL,
                confidence REAL,
                provenance_json TEXT,
                created_at TEXT
            );
            """)

            # 4. Canonical Regions
            cur.execute("""
            CREATE TABLE IF NOT EXISTS regions (
                canonical_region_id TEXT PRIMARY KEY,
                name TEXT,
                geometry_json TEXT,
                bbox_json TEXT,
                observed_region_ids_json TEXT,
                first_seen TEXT,
                last_seen TEXT,
                description TEXT,
                tags_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );
            """)

            # 5. EO Events
            cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                title TEXT,
                canonical_region_id TEXT,
                semantic_class TEXT,
                state TEXT,
                confidence REAL,
                confidence_dimensions_json TEXT,
                first_seen TEXT,
                last_seen TEXT,
                supporting_findings_json TEXT,
                supporting_analyses_json TEXT,
                geometry_json TEXT,
                bbox_json TEXT,
                history_json TEXT,
                metadata_json TEXT,
                version INTEGER,
                created_at TEXT,
                updated_at TEXT
            );
            """)

            # 6. Event Findings Link Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS event_findings (
                event_id TEXT,
                finding_id TEXT,
                added_at TEXT,
                PRIMARY KEY (event_id, finding_id)
            );
            """)

            # 7. Region Lineage
            cur.execute("""
            CREATE TABLE IF NOT EXISTS region_lineage (
                lineage_id TEXT PRIMARY KEY,
                parent_region_id TEXT,
                child_region_id TEXT,
                relationship_type TEXT,
                metadata_json TEXT,
                created_at TEXT
            );
            """)

            # 8. Event Relationships
            cur.execute("""
            CREATE TABLE IF NOT EXISTS event_relationships (
                relationship_id TEXT PRIMARY KEY,
                source_event_id TEXT,
                target_event_id TEXT,
                relationship_type TEXT,
                weight REAL,
                metadata_json TEXT,
                created_at TEXT
            );
            """)

            # 9. Investigation Templates
            cur.execute("""
            CREATE TABLE IF NOT EXISTS investigation_templates (
                template_id TEXT PRIMARY KEY,
                name TEXT,
                question TEXT,
                analysis_mode TEXT,
                required_evidence_json TEXT,
                time_configuration_json TEXT,
                semantic_targets_json TEXT,
                filters_json TEXT,
                created_at TEXT
            );
            """)

            # 10. Monitor Definitions
            cur.execute("""
            CREATE TABLE IF NOT EXISTS monitor_definitions (
                monitor_id TEXT PRIMARY KEY,
                name TEXT,
                aoi_json TEXT,
                bbox_json TEXT,
                observation_collection TEXT,
                schedule_cadence TEXT,
                template_id TEXT,
                trigger_condition_json TEXT,
                enabled INTEGER,
                max_runs INTEGER,
                cooldown_hours INTEGER,
                created_at TEXT,
                updated_at TEXT
            );
            """)

            # 11. Monitor Runs
            cur.execute("""
            CREATE TABLE IF NOT EXISTS monitor_runs (
                run_id TEXT PRIMARY KEY,
                monitor_id TEXT,
                observation_id TEXT,
                status TEXT,
                analysis_run_id TEXT,
                triggered INTEGER,
                alert_id TEXT,
                error_category TEXT,
                error_message TEXT,
                executed_at TEXT
            );
            """)

            # 12. Monitor Alerts
            cur.execute("""
            CREATE TABLE IF NOT EXISTS monitor_alerts (
                alert_id TEXT PRIMARY KEY,
                monitor_id TEXT,
                event_id TEXT,
                finding_id TEXT,
                severity TEXT,
                trigger_reason TEXT,
                alert_fingerprint TEXT,
                evidence_json TEXT,
                acknowledged INTEGER,
                created_at TEXT
            );
            """)

            # 13. Baselines
            cur.execute("""
            CREATE TABLE IF NOT EXISTS baselines (
                baseline_id TEXT PRIMARY KEY,
                metric_name TEXT,
                spatial_unit TEXT,
                temporal_window TEXT,
                seasonal_grouping TEXT,
                sample_count INTEGER,
                mean REAL,
                std REAL,
                median REAL,
                mad REAL,
                p90 REAL,
                min_val REAL,
                max_val REAL,
                version TEXT,
                created_at TEXT
            );
            """)

            # 14. Anomalies
            cur.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                anomaly_id TEXT PRIMARY KEY,
                baseline_id TEXT,
                region_id TEXT,
                event_id TEXT,
                finding_id TEXT,
                metric_name TEXT,
                observed_value REAL,
                baseline_mean REAL,
                baseline_std REAL,
                baseline_range_json TEXT,
                anomaly_score REAL,
                confidence REAL,
                anomaly_type TEXT,
                explanation TEXT,
                status TEXT,
                created_at TEXT
            );
            """)

            # 15. Saved Searches & Regions
            cur.execute("""
            CREATE TABLE IF NOT EXISTS saved_searches (
                search_id TEXT PRIMARY KEY,
                name TEXT,
                query TEXT,
                filters_json TEXT,
                created_at TEXT
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS saved_regions (
                saved_region_id TEXT PRIMARY KEY,
                region_id TEXT,
                name TEXT,
                aoi_json TEXT,
                bbox_json TEXT,
                description TEXT,
                tags_json TEXT,
                created_at TEXT
            );
            """)

            # Indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_findings_inv ON findings (investigation_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_findings_sem ON findings (semantic_class);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_events_reg ON events (canonical_region_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_events_state ON events (state);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_events_sem ON events (semantic_class);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_events_upd ON events (updated_at);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_mon ON monitor_alerts (monitor_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_fp ON monitor_alerts (alert_fingerprint);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_mruns_mon ON monitor_runs (monitor_id, observation_id);")

            conn.commit()
            conn.close()

    # --- Findings CRUD ---

    def save_finding(self, finding: PersistentFinding, fingerprint: Optional[str] = None) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO findings (
                finding_id, investigation_id, type, label, geometry_json, bbox_json,
                confidence, evidence_ids_json, observation_ids_json, metrics_json,
                semantic_class, fingerprint, model_provenance_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                finding.finding_id,
                finding.investigation_id,
                finding.type,
                finding.label,
                json.dumps(finding.geometry),
                json.dumps(finding.bounding_box),
                finding.confidence,
                json.dumps(finding.evidence_ids),
                json.dumps(finding.observation_ids),
                json.dumps(finding.metrics),
                finding.semantic_class,
                fingerprint or finding.finding_id,
                json.dumps(finding.model_provenance),
                finding.created_at,
            ))
            conn.commit()
            conn.close()
            return True

    def get_finding(self, finding_id: str) -> Optional[PersistentFinding]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM findings WHERE finding_id = ?;", (finding_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return self._row_to_finding(row)

    def list_findings(
        self,
        investigation_id: Optional[str] = None,
        semantic_class: Optional[str] = None,
        limit: int = 50,
    ) -> List[PersistentFinding]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            query = "SELECT * FROM findings WHERE 1=1"
            params = []
            if investigation_id:
                query += " AND investigation_id = ?"
                params.append(investigation_id)
            if semantic_class:
                query += " AND semantic_class = ?"
                params.append(semantic_class)
            query += " ORDER BY created_at DESC LIMIT ?;"
            params.append(limit)
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            conn.close()
            return [self._row_to_finding(r) for r in rows]

    def _row_to_finding(self, row: sqlite3.Row) -> PersistentFinding:
        return PersistentFinding(
            finding_id=row["finding_id"],
            investigation_id=row["investigation_id"],
            type=row["type"],
            label=row["label"],
            geometry=json.loads(row["geometry_json"] or "{}"),
            bounding_box=json.loads(row["bbox_json"] or "[]"),
            confidence=row["confidence"],
            evidence_ids=json.loads(row["evidence_ids_json"] or "[]"),
            observation_ids=json.loads(row["observation_ids_json"] or "[]"),
            metrics=json.loads(row["metrics_json"] or "{}"),
            semantic_class=row["semantic_class"],
            created_at=row["created_at"],
            model_provenance=json.loads(row["model_provenance_json"] or "{}"),
        )

    # --- Regions CRUD ---

    def save_region(self, region: CanonicalRegion) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO regions (
                canonical_region_id, name, geometry_json, bbox_json,
                observed_region_ids_json, first_seen, last_seen,
                description, tags_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                region.canonical_region_id,
                region.name,
                json.dumps(region.geometry),
                json.dumps(region.bounding_box),
                json.dumps(region.observed_region_ids),
                region.first_seen,
                region.last_seen,
                region.description,
                json.dumps(region.tags),
                region.created_at,
                region.updated_at,
            ))
            conn.commit()
            conn.close()
            return True

    def get_region(self, canonical_region_id: str) -> Optional[CanonicalRegion]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM regions WHERE canonical_region_id = ?;", (canonical_region_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return self._row_to_region(row)

    def list_regions(self, limit: int = 100) -> List[CanonicalRegion]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM regions ORDER BY updated_at DESC LIMIT ?;", (limit,))
            rows = cur.fetchall()
            conn.close()
            return [self._row_to_region(r) for r in rows]

    def _row_to_region(self, row: sqlite3.Row) -> CanonicalRegion:
        return CanonicalRegion(
            canonical_region_id=row["canonical_region_id"],
            name=row["name"],
            geometry=json.loads(row["geometry_json"] or "{}"),
            bounding_box=json.loads(row["bbox_json"] or "[]"),
            observed_region_ids=json.loads(row["observed_region_ids_json"] or "[]"),
            first_seen=row["first_seen"],
            last_seen=row["last_seen"],
            description=row["description"],
            tags=json.loads(row["tags_json"] or "[]"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # --- Events CRUD ---

    def save_event(self, event: EOEvent) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO events (
                event_id, title, canonical_region_id, semantic_class, state,
                confidence, confidence_dimensions_json, first_seen, last_seen,
                supporting_findings_json, supporting_analyses_json, geometry_json,
                bbox_json, history_json, metadata_json, version, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                event.event_id,
                event.title,
                event.canonical_region_id,
                event.semantic_class,
                event.state.value if hasattr(event.state, "value") else str(event.state),
                event.confidence,
                json.dumps(event.confidence_dimensions),
                event.first_seen,
                event.last_seen,
                json.dumps(event.supporting_findings),
                json.dumps(event.supporting_analyses),
                json.dumps(event.geometry),
                json.dumps(event.bounding_box),
                json.dumps(event.history),
                json.dumps(event.metadata),
                event.version,
                event.created_at,
                event.updated_at,
            ))

            # Maintain event_findings join table
            for fid in event.supporting_findings:
                cur.execute("""
                INSERT OR IGNORE INTO event_findings (event_id, finding_id, added_at)
                VALUES (?, ?, ?);
                """, (event.event_id, fid, datetime.utcnow().isoformat()))

            conn.commit()
            conn.close()
            return True

    def get_event(self, event_id: str) -> Optional[EOEvent]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM events WHERE event_id = ?;", (event_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return self._row_to_event(row)

    def list_events(
        self,
        state: Optional[str] = None,
        semantic_class: Optional[str] = None,
        region_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[EOEvent]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            if state:
                query += " AND state = ?"
                params.append(state)
            if semantic_class:
                query += " AND semantic_class = ?"
                params.append(semantic_class)
            if region_id:
                query += " AND canonical_region_id = ?"
                params.append(region_id)
            query += " ORDER BY updated_at DESC LIMIT ?;"
            params.append(limit)
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            conn.close()
            return [self._row_to_event(r) for r in rows]

    def update_event_state(
        self,
        event_id: str,
        new_state: EventState,
        reason: str,
        finding_id: Optional[str] = None,
    ) -> bool:
        event = self.get_event(event_id)
        if not event:
            return False

        old_state_str = event.state.value if hasattr(event.state, "value") else str(event.state)
        new_state_str = new_state.value if hasattr(new_state, "value") else str(new_state)

        event.state = new_state
        event.version += 1
        now = datetime.utcnow().isoformat()
        event.updated_at = now
        event.history.append({
            "timestamp": now,
            "from_state": old_state_str,
            "to_state": new_state_str,
            "reason": reason,
            "finding_id": finding_id,
        })
        return self.save_event(event)

    def _row_to_event(self, row: sqlite3.Row) -> EOEvent:
        return EOEvent(
            event_id=row["event_id"],
            title=row["title"],
            canonical_region_id=row["canonical_region_id"],
            semantic_class=row["semantic_class"],
            state=EventState(row["state"]),
            confidence=row["confidence"],
            confidence_dimensions=json.loads(row["confidence_dimensions_json"] or "{}"),
            first_seen=row["first_seen"],
            last_seen=row["last_seen"],
            supporting_findings=json.loads(row["supporting_findings_json"] or "[]"),
            supporting_analyses=json.loads(row["supporting_analyses_json"] or "[]"),
            geometry=json.loads(row["geometry_json"] or "{}"),
            bounding_box=json.loads(row["bbox_json"] or "[]"),
            history=json.loads(row["history_json"] or "[]"),
            metadata=json.loads(row["metadata_json"] or "{}"),
            version=row["version"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # --- Region Lineage ---

    def save_lineage(self, lineage: RegionLineage) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO region_lineage (
                lineage_id, parent_region_id, child_region_id, relationship_type, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?);
            """, (
                lineage.lineage_id,
                lineage.parent_region_id,
                lineage.child_region_id,
                lineage.relationship_type,
                json.dumps(lineage.metadata),
                lineage.created_at,
            ))
            conn.commit()
            conn.close()
            return True

    def get_region_lineage(self, region_id: str) -> List[RegionLineage]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            SELECT * FROM region_lineage
            WHERE parent_region_id = ? OR child_region_id = ?
            ORDER BY created_at DESC;
            """, (region_id, region_id))
            rows = cur.fetchall()
            conn.close()
            return [
                RegionLineage(
                    lineage_id=r["lineage_id"],
                    parent_region_id=r["parent_region_id"],
                    child_region_id=r["child_region_id"],
                    relationship_type=r["relationship_type"],
                    metadata=json.loads(r["metadata_json"] or "{}"),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # --- Investigation Templates ---

    def save_template(self, template: InvestigationTemplate) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO investigation_templates (
                template_id, name, question, analysis_mode, required_evidence_json,
                time_configuration_json, semantic_targets_json, filters_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                template.template_id,
                template.name,
                template.question,
                template.analysis_mode,
                json.dumps(template.required_evidence),
                json.dumps(template.time_configuration),
                json.dumps(template.semantic_targets),
                json.dumps(template.filters),
                template.created_at,
            ))
            conn.commit()
            conn.close()
            return True

    def get_template(self, template_id: str) -> Optional[InvestigationTemplate]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM investigation_templates WHERE template_id = ?;", (template_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return InvestigationTemplate(
                template_id=row["template_id"],
                name=row["name"],
                question=row["question"],
                analysis_mode=row["analysis_mode"],
                required_evidence=json.loads(row["required_evidence_json"] or "[]"),
                time_configuration=json.loads(row["time_configuration_json"] or "{}"),
                semantic_targets=json.loads(row["semantic_targets_json"] or "[]"),
                filters=json.loads(row["filters_json"] or "{}"),
                created_at=row["created_at"],
            )

    def list_templates(self) -> List[InvestigationTemplate]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM investigation_templates ORDER BY created_at DESC;")
            rows = cur.fetchall()
            conn.close()
            return [
                InvestigationTemplate(
                    template_id=r["template_id"],
                    name=r["name"],
                    question=r["question"],
                    analysis_mode=r["analysis_mode"],
                    required_evidence=json.loads(r["required_evidence_json"] or "[]"),
                    time_configuration=json.loads(r["time_configuration_json"] or "{}"),
                    semantic_targets=json.loads(r["semantic_targets_json"] or "[]"),
                    filters=json.loads(r["filters_json"] or "{}"),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # --- Monitors & Alerts ---

    def save_monitor(self, monitor: MonitorDefinition) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO monitor_definitions (
                monitor_id, name, aoi_json, bbox_json, observation_collection,
                schedule_cadence, template_id, trigger_condition_json, enabled,
                max_runs, cooldown_hours, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                monitor.monitor_id,
                monitor.name,
                json.dumps(monitor.aoi),
                json.dumps(monitor.bounding_box),
                monitor.observation_collection,
                monitor.schedule_cadence,
                monitor.template_id,
                json.dumps(monitor.trigger_condition),
                1 if monitor.enabled else 0,
                monitor.max_runs,
                monitor.cooldown_hours,
                monitor.created_at,
                monitor.updated_at,
            ))
            conn.commit()
            conn.close()
            return True

    def get_monitor(self, monitor_id: str) -> Optional[MonitorDefinition]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM monitor_definitions WHERE monitor_id = ?;", (monitor_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return self._row_to_monitor(row)

    def list_monitors(self, enabled_only: bool = False) -> List[MonitorDefinition]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            query = "SELECT * FROM monitor_definitions"
            if enabled_only:
                query += " WHERE enabled = 1"
            query += " ORDER BY updated_at DESC;"
            cur.execute(query)
            rows = cur.fetchall()
            conn.close()
            return [self._row_to_monitor(r) for r in rows]

    def _row_to_monitor(self, row: sqlite3.Row) -> MonitorDefinition:
        return MonitorDefinition(
            monitor_id=row["monitor_id"],
            name=row["name"],
            aoi=json.loads(row["aoi_json"] or "{}"),
            bounding_box=json.loads(row["bbox_json"] or "[]"),
            observation_collection=row["observation_collection"],
            schedule_cadence=row["schedule_cadence"],
            template_id=row["template_id"],
            trigger_condition=json.loads(row["trigger_condition_json"] or "{}"),
            enabled=bool(row["enabled"]),
            max_runs=row["max_runs"],
            cooldown_hours=row["cooldown_hours"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_monitor_run(self, run: MonitorRun) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO monitor_runs (
                run_id, monitor_id, observation_id, status, analysis_run_id,
                triggered, alert_id, error_category, error_message, executed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                run.run_id,
                run.monitor_id,
                run.observation_id,
                run.status,
                run.analysis_run_id,
                1 if run.triggered else 0,
                run.alert_id,
                run.error_category,
                run.error_message,
                run.executed_at,
            ))
            conn.commit()
            conn.close()
            return True

    def list_monitor_runs(self, monitor_id: str, limit: int = 20) -> List[MonitorRun]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            SELECT * FROM monitor_runs WHERE monitor_id = ? ORDER BY executed_at DESC LIMIT ?;
            """, (monitor_id, limit))
            rows = cur.fetchall()
            conn.close()
            return [
                MonitorRun(
                    run_id=r["run_id"],
                    monitor_id=r["monitor_id"],
                    observation_id=r["observation_id"],
                    status=r["status"],
                    analysis_run_id=r["analysis_run_id"],
                    triggered=bool(r["triggered"]),
                    alert_id=r["alert_id"],
                    error_category=r["error_category"],
                    error_message=r["error_message"],
                    executed_at=r["executed_at"],
                )
                for r in rows
            ]

    def has_processed_observation(self, monitor_id: str, observation_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            SELECT COUNT(*) as cnt FROM monitor_runs
            WHERE monitor_id = ? AND observation_id = ? AND status IN ('COMPLETED', 'PROCESSING');
            """, (monitor_id, observation_id))
            row = cur.fetchone()
            conn.close()
            return bool(row["cnt"] > 0) if row else False

    def save_monitor_alert(self, alert: MonitorAlert) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO monitor_alerts (
                alert_id, monitor_id, event_id, finding_id, severity,
                trigger_reason, alert_fingerprint, evidence_json, acknowledged, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                alert.alert_id,
                alert.monitor_id,
                alert.event_id,
                alert.finding_id,
                alert.severity,
                alert.trigger_reason,
                alert.alert_fingerprint,
                json.dumps(alert.evidence),
                1 if alert.acknowledged else 0,
                alert.created_at,
            ))
            conn.commit()
            conn.close()
            return True

    def has_alert_fingerprint(self, fingerprint: str) -> bool:
        if not fingerprint:
            return False
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as cnt FROM monitor_alerts WHERE alert_fingerprint = ?;", (fingerprint,))
            row = cur.fetchone()
            conn.close()
            return bool(row["cnt"] > 0) if row else False

    def list_monitor_alerts(self, monitor_id: Optional[str] = None, limit: int = 50) -> List[MonitorAlert]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            query = "SELECT * FROM monitor_alerts"
            params = []
            if monitor_id:
                query += " WHERE monitor_id = ?"
                params.append(monitor_id)
            query += " ORDER BY created_at DESC LIMIT ?;"
            params.append(limit)
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            conn.close()
            return [
                MonitorAlert(
                    alert_id=r["alert_id"],
                    monitor_id=r["monitor_id"],
                    event_id=r["event_id"],
                    finding_id=r["finding_id"],
                    severity=r["severity"],
                    trigger_reason=r["trigger_reason"],
                    alert_fingerprint=r["alert_fingerprint"],
                    evidence=json.loads(r["evidence_json"] or "{}"),
                    acknowledged=bool(r["acknowledged"]),
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def save_alert(self, alert: MonitorAlert) -> bool:
        return self.save_monitor_alert(alert)

    def list_alerts(self, monitor_id: Optional[str] = None, limit: int = 50) -> List[MonitorAlert]:
        return self.list_monitor_alerts(monitor_id=monitor_id, limit=limit)

    def alert_fingerprint_exists(self, fingerprint: str) -> bool:
        return self.has_alert_fingerprint(fingerprint)

    def acknowledge_alert(self, alert_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE monitor_alerts SET acknowledged = 1 WHERE alert_id = ?;", (alert_id,))
            affected = cur.rowcount
            conn.commit()
            conn.close()
            return affected > 0

    # --- Baselines & Anomalies ---

    def save_baseline(self, baseline: Baseline) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO baselines (
                baseline_id, metric_name, spatial_unit, temporal_window, seasonal_grouping,
                sample_count, mean, std, median, mad, p90, min_val, max_val, version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                baseline.baseline_id,
                baseline.metric_name,
                baseline.spatial_unit,
                baseline.temporal_window,
                baseline.seasonal_grouping,
                baseline.sample_count,
                baseline.mean,
                baseline.std,
                baseline.median,
                baseline.mad,
                baseline.p90,
                baseline.min_val,
                baseline.max_val,
                baseline.version,
                baseline.created_at,
            ))
            conn.commit()
            conn.close()
            return True

    def get_baseline(self, baseline_id: str) -> Optional[Baseline]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM baselines WHERE baseline_id = ?;", (baseline_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return self._row_to_baseline(row)

    def find_baseline(
        self,
        metric_name: str,
        spatial_unit: str = "general",
        seasonal_grouping: Optional[str] = None,
    ) -> Optional[Baseline]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            query = "SELECT * FROM baselines WHERE metric_name = ?"
            params = [metric_name]
            if seasonal_grouping:
                query += " AND seasonal_grouping = ?"
                params.append(seasonal_grouping)
            query += " ORDER BY created_at DESC LIMIT 1;"
            cur.execute(query, tuple(params))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return self._row_to_baseline(row)

    def _row_to_baseline(self, row: sqlite3.Row) -> Baseline:
        return Baseline(
            baseline_id=row["baseline_id"],
            metric_name=row["metric_name"],
            spatial_unit=row["spatial_unit"],
            temporal_window=row["temporal_window"],
            sample_count=row["sample_count"],
            mean=row["mean"],
            std=row["std"],
            median=row["median"],
            mad=row["mad"],
            p90=row["p90"],
            min_val=row["min_val"],
            max_val=row["max_val"],
            seasonal_grouping=row["seasonal_grouping"],
            version=row["version"],
            created_at=row["created_at"],
        )

    def save_anomaly(self, anomaly: AnomalyRecord) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO anomalies (
                anomaly_id, baseline_id, region_id, event_id, finding_id,
                metric_name, observed_value, baseline_mean, baseline_std,
                baseline_range_json, anomaly_score, confidence, anomaly_type,
                explanation, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                anomaly.anomaly_id,
                anomaly.baseline_id,
                anomaly.region_id,
                anomaly.event_id,
                anomaly.finding_id,
                anomaly.metric_name,
                anomaly.observed_value,
                anomaly.baseline_mean,
                anomaly.baseline_std,
                json.dumps(anomaly.baseline_range),
                anomaly.anomaly_score,
                anomaly.confidence,
                anomaly.anomaly_type,
                anomaly.explanation,
                anomaly.status,
                anomaly.created_at,
            ))
            conn.commit()
            conn.close()
            return True

    def list_anomalies(
        self,
        status: Optional[str] = None,
        region_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[AnomalyRecord]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            query = "SELECT * FROM anomalies WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            if region_id:
                query += " AND region_id = ?"
                params.append(region_id)
            query += " ORDER BY created_at DESC LIMIT ?;"
            params.append(limit)
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
            conn.close()
            return [
                AnomalyRecord(
                    anomaly_id=r["anomaly_id"],
                    baseline_id=r["baseline_id"],
                    region_id=r["region_id"],
                    event_id=r["event_id"],
                    finding_id=r["finding_id"],
                    metric_name=r["metric_name"],
                    observed_value=r["observed_value"],
                    baseline_mean=r["baseline_mean"],
                    baseline_std=r["baseline_std"],
                    baseline_range=json.loads(r["baseline_range_json"] or "[]"),
                    anomaly_score=r["anomaly_score"],
                    confidence=r["confidence"],
                    anomaly_type=r["anomaly_type"],
                    explanation=r["explanation"],
                    status=r["status"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    # --- Saved Searches & Saved Regions ---

    def save_saved_search(self, search_id: str, name: str, query: str, filters: Dict[str, Any]) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO saved_searches (search_id, name, query, filters_json, created_at)
            VALUES (?, ?, ?, ?, ?);
            """, (search_id, name, query, json.dumps(filters), datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            return True

    def list_saved_searches(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM saved_searches ORDER BY created_at DESC;")
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "search_id": r["search_id"],
                    "name": r["name"],
                    "query": r["query"],
                    "filters": json.loads(r["filters_json"] or "{}"),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def delete_saved_search(self, search_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM saved_searches WHERE search_id = ?;", (search_id,))
            conn.commit()
            conn.close()
            return True

    def save_saved_region(
        self,
        saved_region_id: str,
        name: str,
        aoi: Dict[str, Any],
        bounding_box: Optional[List[float]] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO saved_regions (
                saved_region_id, region_id, name, aoi_json, bbox_json, description, tags_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                saved_region_id,
                saved_region_id,
                name,
                json.dumps(aoi),
                json.dumps(bounding_box or []),
                description,
                json.dumps(tags or []),
                datetime.utcnow().isoformat(),
            ))
            conn.commit()
            conn.close()
            return True

    def list_saved_regions(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM saved_regions ORDER BY created_at DESC;")
            rows = cur.fetchall()
            conn.close()
            return [
                {
                    "saved_region_id": r["saved_region_id"],
                    "region_id": r["region_id"],
                    "name": r["name"],
                    "aoi": json.loads(r["aoi_json"] or "{}"),
                    "bounding_box": json.loads(r["bbox_json"] or "[]"),
                    "description": r["description"],
                    "tags": json.loads(r["tags_json"] or "[]"),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def delete_saved_region(self, saved_region_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM saved_regions WHERE saved_region_id = ?;", (saved_region_id,))
            conn.commit()
            conn.close()
            return True


# Global default instance
intelligence_repo = IntelligenceRepository()
