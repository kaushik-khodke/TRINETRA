"""
TRINETRA Phase 8 — Durable SQLite Workspace Repository
Thread-safe, indexed, ACID-compliant persistence for analyst workspaces, plans,
comparisons, evidence boards, annotations, reviews, follow-ups, reports, and task queue.
"""

import sqlite3
import json
import threading
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from backend.config.settings import settings
except ImportError:
    from config.settings import settings

from .models import (
    Workspace,
    WorkspaceStatus,
    WorkspaceContext,
    WorkspaceActivity,
    InvestigationPlan,
    InvestigationStep,
    PlanStepType,
    PlanStatus,
    StepStatus,
    InvestigationPlanRun,
    BatchJob,
    RegionComparison,
    AnalysisScenario,
    EvidenceBoardItem,
    EvidenceBoardRelation,
    Annotation,
    ReviewRecord,
    ReviewStatus,
    FollowUp,
    ReportClaim,
    ReportSection,
    ReportDocument,
    ReportStatus,
    WorkspaceTask,
    TaskPriority,
    TaskStatus,
    WorkspaceSnapshot,
)


class WorkspaceRepository:
    """
    Durable storage engine for TRINETRA Analyst Workspaces.
    Supports file-based SQLite and isolated in-memory (:memory:) databases for testing.
    """

    def __init__(self, db_path: Optional[str] = None):
        raw_path = db_path or getattr(settings, "workspace_db_path", os.path.join(settings.outputs_dir, "workspace.db"))
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

            # 1. Workspaces
            cur.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                workspace_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                current_aoi_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_by TEXT
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_workspaces_status ON workspaces(status)")

            # 2. Workspace Contexts
            cur.execute("""
            CREATE TABLE IF NOT EXISTS workspace_contexts (
                workspace_id TEXT PRIMARY KEY,
                current_aoi_json TEXT,
                active_regions_json TEXT,
                selected_observations_json TEXT,
                selected_events_json TEXT,
                selected_findings_json TEXT,
                open_investigation_id TEXT,
                active_comparison_id TEXT,
                active_report_id TEXT
            )
            """)

            # 3. Workspace Activities
            cur.execute("""
            CREATE TABLE IF NOT EXISTS workspace_activities (
                activity_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                details_json TEXT,
                timestamp TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_activities_ws ON workspace_activities(workspace_id, timestamp DESC)")

            # 4. Investigation Plans
            cur.execute("""
            CREATE TABLE IF NOT EXISTS investigation_plans (
                plan_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                title TEXT NOT NULL,
                question TEXT NOT NULL,
                steps_json TEXT NOT NULL,
                constraints_json TEXT,
                required_evidence_json TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_plans_ws ON investigation_plans(workspace_id)")

            # 5. Investigation Plan Runs
            cur.execute("""
            CREATE TABLE IF NOT EXISTS investigation_plan_runs (
                run_id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                execution_index INTEGER NOT NULL,
                status TEXT NOT NULL,
                step_results_json TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_plan_runs_plan ON investigation_plan_runs(plan_id)")

            # 6. Batch Jobs
            cur.execute("""
            CREATE TABLE IF NOT EXISTS batch_jobs (
                batch_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                template_id TEXT NOT NULL,
                targets_json TEXT NOT NULL,
                status TEXT NOT NULL,
                concurrency INTEGER NOT NULL,
                results_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_batch_ws ON batch_jobs(workspace_id)")

            # 7. Region Comparisons
            cur.execute("""
            CREATE TABLE IF NOT EXISTS region_comparisons (
                comparison_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                region_a_id TEXT NOT NULL,
                region_b_id TEXT NOT NULL,
                period TEXT NOT NULL,
                metrics_json TEXT,
                differences_json TEXT,
                warnings_json TEXT,
                created_at TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_comparisons_ws ON region_comparisons(workspace_id)")

            # 8. Analysis Scenarios
            cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_scenarios (
                scenario_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                base_run_id TEXT NOT NULL,
                parameter_overrides_json TEXT NOT NULL,
                results_json TEXT,
                difference_summary TEXT,
                created_at TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_scenarios_ws ON analysis_scenarios(workspace_id)")

            # 9. Evidence Board Items
            cur.execute("""
            CREATE TABLE IF NOT EXISTS evidence_board_items (
                item_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                position_x REAL NOT NULL,
                position_y REAL NOT NULL,
                title TEXT,
                annotation TEXT,
                created_at TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_board_items_ws ON evidence_board_items(workspace_id)")

            # 10. Evidence Board Relations
            cur.execute("""
            CREATE TABLE IF NOT EXISTS evidence_board_relations (
                relation_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                source_item_id TEXT NOT NULL,
                target_item_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                metadata_json TEXT,
                created_at TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_board_rels_ws ON evidence_board_relations(workspace_id)")

            # 11. Annotations
            cur.execute("""
            CREATE TABLE IF NOT EXISTS annotations (
                annotation_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                geometry_json TEXT,
                text TEXT NOT NULL,
                type TEXT NOT NULL,
                linked_entity_type TEXT,
                linked_entity_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_annotations_ws ON annotations(workspace_id)")

            # 12. Review Records
            cur.execute("""
            CREATE TABLE IF NOT EXISTS review_records (
                review_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                status TEXT NOT NULL,
                review_note TEXT,
                reviewed_at TEXT NOT NULL,
                analyst_id TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_ws ON review_records(workspace_id)")

            # 13. Follow-ups
            cur.execute("""
            CREATE TABLE IF NOT EXISTS follow_ups (
                follow_up_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                linked_entity_type TEXT NOT NULL,
                linked_entity_id TEXT NOT NULL,
                note TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_followups_ws ON follow_ups(workspace_id, status)")

            # 14. Report Documents
            cur.execute("""
            CREATE TABLE IF NOT EXISTS report_documents (
                report_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                sections_json TEXT NOT NULL,
                version INTEGER NOT NULL,
                manifest_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_reports_ws ON report_documents(workspace_id)")

            # 15. Workspace Tasks
            cur.execute("""
            CREATE TABLE IF NOT EXISTS workspace_tasks (
                task_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                type TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                progress_json TEXT NOT NULL,
                result_reference TEXT,
                error_json TEXT,
                idempotency_key TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_ws ON workspace_tasks(workspace_id, status)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_idem ON workspace_tasks(idempotency_key)")

            # 16. Workspace Snapshots
            cur.execute("""
            CREATE TABLE IF NOT EXISTS workspace_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_ws ON workspace_snapshots(workspace_id)")

            conn.commit()
            conn.close()

    # =========================================================================
    # Workspace Operations
    # =========================================================================

    def save_workspace(self, ws: Workspace) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO workspaces (
                workspace_id, name, description, status, current_aoi_json, created_at, updated_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ws.workspace_id,
                ws.name,
                ws.description,
                ws.status.value if isinstance(ws.status, WorkspaceStatus) else str(ws.status),
                json.dumps(ws.current_aoi or {}),
                ws.created_at,
                ws.updated_at,
                ws.created_by,
            ))
            conn.commit()
            conn.close()

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM workspaces WHERE workspace_id = ?", (workspace_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return Workspace(
            workspace_id=row["workspace_id"],
            name=row["name"],
            description=row["description"] or "",
            status=WorkspaceStatus(row["status"]),
            current_aoi=json.loads(row["current_aoi_json"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"] or "analyst",
        )

    def list_workspaces(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Workspace]:
        conn = self._get_connection()
        cur = conn.cursor()
        query = "SELECT * FROM workspaces"
        params: List[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return [
            Workspace(
                workspace_id=row["workspace_id"],
                name=row["name"],
                description=row["description"] or "",
                status=WorkspaceStatus(row["status"]),
                current_aoi=json.loads(row["current_aoi_json"] or "{}"),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                created_by=row["created_by"] or "analyst",
            )
            for row in rows
        ]

    def delete_workspace(self, workspace_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM workspaces WHERE workspace_id = ?", (workspace_id,))
            deleted = cur.rowcount > 0
            if deleted:
                for tbl in [
                    "workspace_contexts", "workspace_activities", "investigation_plans",
                    "batch_jobs", "region_comparisons", "analysis_scenarios",
                    "evidence_board_items", "evidence_board_relations", "annotations",
                    "review_records", "follow_ups", "report_documents", "workspace_tasks",
                    "workspace_snapshots"
                ]:
                    cur.execute(f"DELETE FROM {tbl} WHERE workspace_id = ?", (workspace_id,))
            conn.commit()
            conn.close()
            return deleted

    # =========================================================================
    # Workspace Context Operations
    # =========================================================================

    def save_context(self, ctx: WorkspaceContext) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO workspace_contexts (
                workspace_id, current_aoi_json, active_regions_json, selected_observations_json,
                selected_events_json, selected_findings_json, open_investigation_id,
                active_comparison_id, active_report_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ctx.workspace_id,
                json.dumps(ctx.current_aoi or {}),
                json.dumps(ctx.active_regions or []),
                json.dumps(ctx.selected_observations or []),
                json.dumps(ctx.selected_events or []),
                json.dumps(ctx.selected_findings or []),
                ctx.open_investigation_id,
                ctx.active_comparison_id,
                ctx.active_report_id,
            ))
            conn.commit()
            conn.close()

    def get_context(self, workspace_id: str) -> Optional[WorkspaceContext]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM workspace_contexts WHERE workspace_id = ?", (workspace_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return WorkspaceContext(
            workspace_id=row["workspace_id"],
            current_aoi=json.loads(row["current_aoi_json"] or "{}"),
            active_regions=json.loads(row["active_regions_json"] or "[]"),
            selected_observations=json.loads(row["selected_observations_json"] or "[]"),
            selected_events=json.loads(row["selected_events_json"] or "[]"),
            selected_findings=json.loads(row["selected_findings_json"] or "[]"),
            open_investigation_id=row["open_investigation_id"],
            active_comparison_id=row["active_comparison_id"],
            active_report_id=row["active_report_id"],
        )

    # =========================================================================
    # Activity Tracker Operations
    # =========================================================================

    def save_activity(self, act: WorkspaceActivity) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO workspace_activities (
                activity_id, workspace_id, activity_type, entity_type, entity_id, details_json, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                act.activity_id,
                act.workspace_id,
                act.activity_type,
                act.entity_type,
                act.entity_id,
                json.dumps(act.details or {}),
                act.timestamp,
            ))
            conn.commit()
            conn.close()

    def list_activities(
        self,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0,
        activity_type: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> List[WorkspaceActivity]:
        conn = self._get_connection()
        cur = conn.cursor()
        query = "SELECT * FROM workspace_activities WHERE workspace_id = ?"
        params: List[Any] = [workspace_id]
        if activity_type:
            query += " AND activity_type = ?"
            params.append(activity_type)
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return [
            WorkspaceActivity(
                activity_id=row["activity_id"],
                workspace_id=row["workspace_id"],
                activity_type=row["activity_type"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                details=json.loads(row["details_json"] or "{}"),
                timestamp=row["timestamp"],
            )
            for row in rows
        ]

    # =========================================================================
    # Investigation Plans & Runs
    # =========================================================================

    def save_plan(self, plan: InvestigationPlan) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            steps_data = [s.to_dict() if hasattr(s, "to_dict") else dict(s) for s in plan.steps]
            cur.execute("""
            INSERT OR REPLACE INTO investigation_plans (
                plan_id, workspace_id, title, question, steps_json, constraints_json,
                required_evidence_json, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plan.plan_id,
                plan.workspace_id,
                plan.title,
                plan.question,
                json.dumps(steps_data),
                json.dumps(plan.constraints or {}),
                json.dumps(plan.required_evidence or []),
                plan.status.value if isinstance(plan.status, PlanStatus) else str(plan.status),
                plan.created_at,
                plan.updated_at,
            ))
            conn.commit()
            conn.close()

    def get_plan(self, plan_id: str) -> Optional[InvestigationPlan]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM investigation_plans WHERE plan_id = ?", (plan_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        steps_raw = json.loads(row["steps_json"] or "[]")
        steps = [
            InvestigationStep(
                step_id=s["step_id"],
                type=PlanStepType(s["type"]),
                depends_on=s.get("depends_on", []),
                parameters=s.get("parameters", {}),
                status=StepStatus(s.get("status", "PENDING")),
                result_reference=s.get("result_reference"),
                error=s.get("error"),
            )
            for s in steps_raw
        ]
        return InvestigationPlan(
            plan_id=row["plan_id"],
            workspace_id=row["workspace_id"],
            title=row["title"],
            question=row["question"],
            steps=steps,
            constraints=json.loads(row["constraints_json"] or "{}"),
            required_evidence=json.loads(row["required_evidence_json"] or "[]"),
            status=PlanStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_plans(self, workspace_id: str) -> List[InvestigationPlan]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM investigation_plans WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
        rows = cur.fetchall()
        conn.close()
        plans = []
        for row in rows:
            steps_raw = json.loads(row["steps_json"] or "[]")
            steps = [
                InvestigationStep(
                    step_id=s["step_id"],
                    type=PlanStepType(s["type"]),
                    depends_on=s.get("depends_on", []),
                    parameters=s.get("parameters", {}),
                    status=StepStatus(s.get("status", "PENDING")),
                    result_reference=s.get("result_reference"),
                    error=s.get("error"),
                )
                for s in steps_raw
            ]
            plans.append(InvestigationPlan(
                plan_id=row["plan_id"],
                workspace_id=row["workspace_id"],
                title=row["title"],
                question=row["question"],
                steps=steps,
                constraints=json.loads(row["constraints_json"] or "{}"),
                required_evidence=json.loads(row["required_evidence_json"] or "[]"),
                status=PlanStatus(row["status"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            ))
        return plans

    def save_plan_run(self, run: InvestigationPlanRun) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO investigation_plan_runs (
                run_id, plan_id, execution_index, status, step_results_json, started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                run.run_id,
                run.plan_id,
                run.execution_index,
                run.status.value if isinstance(run.status, PlanStatus) else str(run.status),
                json.dumps(run.step_results or {}),
                run.started_at,
                run.completed_at,
            ))
            conn.commit()
            conn.close()

    def get_plan_run(self, run_id: str) -> Optional[InvestigationPlanRun]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM investigation_plan_runs WHERE run_id = ?", (run_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return InvestigationPlanRun(
            run_id=row["run_id"],
            plan_id=row["plan_id"],
            execution_index=row["execution_index"],
            status=PlanStatus(row["status"]),
            step_results=json.loads(row["step_results_json"] or "{}"),
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    def list_plan_runs(self, plan_id: str) -> List[InvestigationPlanRun]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM investigation_plan_runs WHERE plan_id = ? ORDER BY started_at DESC", (plan_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            InvestigationPlanRun(
                run_id=row["run_id"],
                plan_id=row["plan_id"],
                execution_index=row["execution_index"],
                status=PlanStatus(row["status"]),
                step_results=json.loads(row["step_results_json"] or "{}"),
                started_at=row["started_at"],
                completed_at=row["completed_at"],
            )
            for row in rows
        ]

    # =========================================================================
    # Batch Jobs
    # =========================================================================

    def save_batch_job(self, job: BatchJob) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO batch_jobs (
                batch_id, workspace_id, template_id, targets_json, status, concurrency, results_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.batch_id,
                job.workspace_id,
                job.template_id,
                json.dumps(job.targets or []),
                job.status,
                job.concurrency,
                json.dumps(job.results or {}),
                job.created_at,
                job.updated_at,
            ))
            conn.commit()
            conn.close()

    def get_batch_job(self, batch_id: str) -> Optional[BatchJob]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM batch_jobs WHERE batch_id = ?", (batch_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return BatchJob(
            batch_id=row["batch_id"],
            workspace_id=row["workspace_id"],
            template_id=row["template_id"],
            targets=json.loads(row["targets_json"] or "[]"),
            status=row["status"],
            concurrency=row["concurrency"],
            results=json.loads(row["results_json"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_batch_jobs(self, workspace_id: str) -> List[BatchJob]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM batch_jobs WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            BatchJob(
                batch_id=row["batch_id"],
                workspace_id=row["workspace_id"],
                template_id=row["template_id"],
                targets=json.loads(row["targets_json"] or "[]"),
                status=row["status"],
                concurrency=row["concurrency"],
                results=json.loads(row["results_json"] or "{}"),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    # =========================================================================
    # Region Comparisons & Analysis Scenarios
    # =========================================================================

    def save_comparison(self, comp: RegionComparison) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO region_comparisons (
                comparison_id, workspace_id, region_a_id, region_b_id, period, metrics_json, differences_json, warnings_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comp.comparison_id,
                comp.workspace_id,
                comp.region_a_id,
                comp.region_b_id,
                comp.period,
                json.dumps(comp.metrics or {}),
                json.dumps(comp.differences or {}),
                json.dumps(comp.warnings or []),
                comp.created_at,
            ))
            conn.commit()
            conn.close()

    def get_comparison(self, comparison_id: str) -> Optional[RegionComparison]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM region_comparisons WHERE comparison_id = ?", (comparison_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return RegionComparison(
            comparison_id=row["comparison_id"],
            workspace_id=row["workspace_id"],
            region_a_id=row["region_a_id"],
            region_b_id=row["region_b_id"],
            period=row["period"],
            metrics=json.loads(row["metrics_json"] or "{}"),
            differences=json.loads(row["differences_json"] or "{}"),
            warnings=json.loads(row["warnings_json"] or "[]"),
            created_at=row["created_at"],
        )

    def list_comparisons(self, workspace_id: str) -> List[RegionComparison]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM region_comparisons WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            RegionComparison(
                comparison_id=row["comparison_id"],
                workspace_id=row["workspace_id"],
                region_a_id=row["region_a_id"],
                region_b_id=row["region_b_id"],
                period=row["period"],
                metrics=json.loads(row["metrics_json"] or "{}"),
                differences=json.loads(row["differences_json"] or "{}"),
                warnings=json.loads(row["warnings_json"] or "[]"),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def save_scenario(self, scenario: AnalysisScenario) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO analysis_scenarios (
                scenario_id, workspace_id, base_run_id, parameter_overrides_json, results_json, difference_summary, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                scenario.scenario_id,
                scenario.workspace_id,
                scenario.base_run_id,
                json.dumps(scenario.parameter_overrides or {}),
                json.dumps(scenario.results or {}),
                scenario.difference_summary,
                scenario.created_at,
            ))
            conn.commit()
            conn.close()

    def get_scenario(self, scenario_id: str) -> Optional[AnalysisScenario]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM analysis_scenarios WHERE scenario_id = ?", (scenario_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return AnalysisScenario(
            scenario_id=row["scenario_id"],
            workspace_id=row["workspace_id"],
            base_run_id=row["base_run_id"],
            parameter_overrides=json.loads(row["parameter_overrides_json"] or "{}"),
            results=json.loads(row["results_json"] or "{}"),
            difference_summary=row["difference_summary"] or "",
            created_at=row["created_at"],
        )

    def list_scenarios(self, workspace_id: str) -> List[AnalysisScenario]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM analysis_scenarios WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            AnalysisScenario(
                scenario_id=row["scenario_id"],
                workspace_id=row["workspace_id"],
                base_run_id=row["base_run_id"],
                parameter_overrides=json.loads(row["parameter_overrides_json"] or "{}"),
                results=json.loads(row["results_json"] or "{}"),
                difference_summary=row["difference_summary"] or "",
                created_at=row["created_at"],
            )
            for row in rows
        ]

    # =========================================================================
    # Evidence Board Items & Relations
    # =========================================================================

    def save_board_item(self, item: EvidenceBoardItem) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            pos = item.position or {"x": 100.0, "y": 100.0}
            cur.execute("""
            INSERT OR REPLACE INTO evidence_board_items (
                item_id, workspace_id, type, source_id, position_x, position_y, title, annotation, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.item_id,
                item.workspace_id,
                item.type,
                item.source_id,
                pos.get("x", 100.0),
                pos.get("y", 100.0),
                item.title,
                item.annotation,
                item.created_at,
            ))
            conn.commit()
            conn.close()

    def get_board_item(self, item_id: str) -> Optional[EvidenceBoardItem]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM evidence_board_items WHERE item_id = ?", (item_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return EvidenceBoardItem(
            item_id=row["item_id"],
            workspace_id=row["workspace_id"],
            type=row["type"],
            source_id=row["source_id"],
            position={"x": row["position_x"], "y": row["position_y"]},
            title=row["title"] or "",
            annotation=row["annotation"] or "",
            created_at=row["created_at"],
        )

    def list_board_items(self, workspace_id: str) -> List[EvidenceBoardItem]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM evidence_board_items WHERE workspace_id = ? ORDER BY created_at ASC", (workspace_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            EvidenceBoardItem(
                item_id=row["item_id"],
                workspace_id=row["workspace_id"],
                type=row["type"],
                source_id=row["source_id"],
                position={"x": row["position_x"], "y": row["position_y"]},
                title=row["title"] or "",
                annotation=row["annotation"] or "",
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def delete_board_item(self, item_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM evidence_board_items WHERE item_id = ?", (item_id,))
            deleted = cur.rowcount > 0
            if deleted:
                cur.execute("DELETE FROM evidence_board_relations WHERE source_item_id = ? OR target_item_id = ?", (item_id, item_id))
            conn.commit()
            conn.close()
            return deleted

    def save_board_relation(self, rel: EvidenceBoardRelation) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO evidence_board_relations (
                relation_id, workspace_id, source_item_id, target_item_id, relation_type, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                rel.relation_id,
                rel.workspace_id,
                rel.source_item_id,
                rel.target_item_id,
                rel.relation_type,
                json.dumps(rel.metadata or {}),
                rel.created_at,
            ))
            conn.commit()
            conn.close()

    def list_board_relations(self, workspace_id: str) -> List[EvidenceBoardRelation]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM evidence_board_relations WHERE workspace_id = ? ORDER BY created_at ASC", (workspace_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            EvidenceBoardRelation(
                relation_id=row["relation_id"],
                workspace_id=row["workspace_id"],
                source_item_id=row["source_item_id"],
                target_item_id=row["target_item_id"],
                relation_type=row["relation_type"],
                metadata=json.loads(row["metadata_json"] or "{}"),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def delete_board_relation(self, relation_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM evidence_board_relations WHERE relation_id = ?", (relation_id,))
            deleted = cur.rowcount > 0
            conn.commit()
            conn.close()
            return deleted

    # =========================================================================
    # Annotations, Review Records & Follow-ups
    # =========================================================================

    def save_annotation(self, ann: Annotation) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO annotations (
                annotation_id, workspace_id, geometry_json, text, type, linked_entity_type, linked_entity_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ann.annotation_id,
                ann.workspace_id,
                json.dumps(ann.geometry or {}),
                ann.text,
                ann.type,
                ann.linked_entity_type,
                ann.linked_entity_id,
                ann.created_at,
                ann.updated_at,
            ))
            conn.commit()
            conn.close()

    def list_annotations(self, workspace_id: str) -> List[Annotation]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM annotations WHERE workspace_id = ? ORDER BY created_at ASC", (workspace_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            Annotation(
                annotation_id=row["annotation_id"],
                workspace_id=row["workspace_id"],
                geometry=json.loads(row["geometry_json"] or "{}"),
                text=row["text"],
                type=row["type"],
                linked_entity_type=row["linked_entity_type"],
                linked_entity_id=row["linked_entity_id"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def delete_annotation(self, annotation_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM annotations WHERE annotation_id = ?", (annotation_id,))
            deleted = cur.rowcount > 0
            conn.commit()
            conn.close()
            return deleted

    def save_review(self, rev: ReviewRecord) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO review_records (
                review_id, workspace_id, entity_type, entity_id, status, review_note, reviewed_at, analyst_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rev.review_id,
                rev.workspace_id,
                rev.entity_type,
                rev.entity_id,
                rev.status.value if isinstance(rev.status, ReviewStatus) else str(rev.status),
                rev.review_note,
                rev.reviewed_at,
                rev.analyst_id,
            ))
            conn.commit()
            conn.close()

    def get_review(self, workspace_id: str, entity_type: str, entity_id: str) -> Optional[ReviewRecord]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
        SELECT * FROM review_records WHERE workspace_id = ? AND entity_type = ? AND entity_id = ?
        """, (workspace_id, entity_type, entity_id))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return ReviewRecord(
            review_id=row["review_id"],
            workspace_id=row["workspace_id"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            status=ReviewStatus(row["status"]),
            review_note=row["review_note"] or "",
            reviewed_at=row["reviewed_at"],
            analyst_id=row["analyst_id"],
        )

    def list_reviews(self, workspace_id: str) -> List[ReviewRecord]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM review_records WHERE workspace_id = ? ORDER BY reviewed_at DESC", (workspace_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            ReviewRecord(
                review_id=row["review_id"],
                workspace_id=row["workspace_id"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                status=ReviewStatus(row["status"]),
                review_note=row["review_note"] or "",
                reviewed_at=row["reviewed_at"],
                analyst_id=row["analyst_id"],
            )
            for row in rows
        ]

    def save_follow_up(self, fu: FollowUp) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO follow_ups (
                follow_up_id, workspace_id, linked_entity_type, linked_entity_id, note, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fu.follow_up_id,
                fu.workspace_id,
                fu.linked_entity_type,
                fu.linked_entity_id,
                fu.note,
                fu.status,
                fu.created_at,
                fu.updated_at,
            ))
            conn.commit()
            conn.close()

    def list_follow_ups(self, workspace_id: str, status: Optional[str] = None) -> List[FollowUp]:
        conn = self._get_connection()
        cur = conn.cursor()
        query = "SELECT * FROM follow_ups WHERE workspace_id = ?"
        params: List[Any] = [workspace_id]
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return [
            FollowUp(
                follow_up_id=row["follow_up_id"],
                workspace_id=row["workspace_id"],
                linked_entity_type=row["linked_entity_type"],
                linked_entity_id=row["linked_entity_id"],
                note=row["note"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    # =========================================================================
    # Report Documents
    # =========================================================================

    def save_report(self, report: ReportDocument) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            sections_data = [s.to_dict() if hasattr(s, "to_dict") else dict(s) for s in report.sections]
            cur.execute("""
            INSERT OR REPLACE INTO report_documents (
                report_id, workspace_id, title, status, sections_json, version, manifest_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.report_id,
                report.workspace_id,
                report.title,
                report.status.value if isinstance(report.status, ReportStatus) else str(report.status),
                json.dumps(sections_data),
                report.version,
                json.dumps(report.manifest or {}),
                report.created_at,
                report.updated_at,
            ))
            conn.commit()
            conn.close()

    def get_report(self, report_id: str) -> Optional[ReportDocument]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM report_documents WHERE report_id = ?", (report_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        sections_raw = json.loads(row["sections_json"] or "[]")
        sections = []
        for s in sections_raw:
            claims = [
                ReportClaim(
                    claim_id=c["claim_id"],
                    text=c["text"],
                    evidence_ids=c.get("evidence_ids", []),
                    type=c.get("type", "FINDING"),
                )
                for c in s.get("claims", [])
            ]
            sections.append(ReportSection(
                section_id=s["section_id"],
                type=s["type"],
                title=s["title"],
                content=s.get("content", ""),
                source_ids=s.get("source_ids", []),
                claims=claims,
                author_type=s.get("author_type", "SYSTEM_GENERATED"),
            ))
        return ReportDocument(
            report_id=row["report_id"],
            workspace_id=row["workspace_id"],
            title=row["title"],
            status=ReportStatus(row["status"]),
            sections=sections,
            version=row["version"],
            manifest=json.loads(row["manifest_json"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_reports(self, workspace_id: str) -> List[ReportDocument]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM report_documents WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
        rows = cur.fetchall()
        conn.close()
        reports = []
        for row in rows:
            sections_raw = json.loads(row["sections_json"] or "[]")
            sections = [
                ReportSection(
                    section_id=s["section_id"],
                    type=s["type"],
                    title=s["title"],
                    content=s.get("content", ""),
                    source_ids=s.get("source_ids", []),
                    claims=[
                        ReportClaim(
                            claim_id=c["claim_id"],
                            text=c["text"],
                            evidence_ids=c.get("evidence_ids", []),
                            type=c.get("type", "FINDING"),
                        )
                        for c in s.get("claims", [])
                    ],
                    author_type=s.get("author_type", "SYSTEM_GENERATED"),
                )
                for s in sections_raw
            ]
            reports.append(ReportDocument(
                report_id=row["report_id"],
                workspace_id=row["workspace_id"],
                title=row["title"],
                status=ReportStatus(row["status"]),
                sections=sections,
                version=row["version"],
                manifest=json.loads(row["manifest_json"] or "{}"),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            ))
        return reports

    # =========================================================================
    # Workspace Tasks
    # =========================================================================

    def save_task(self, task: WorkspaceTask) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO workspace_tasks (
                task_id, workspace_id, type, priority, status, progress_json, result_reference, error_json, idempotency_key, created_at, started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id,
                task.workspace_id,
                task.type,
                task.priority.value if isinstance(task.priority, TaskPriority) else str(task.priority),
                task.status.value if isinstance(task.status, TaskStatus) else str(task.status),
                json.dumps(task.progress or {}),
                task.result_reference,
                json.dumps(task.error) if task.error else None,
                task.idempotency_key,
                task.created_at,
                task.started_at,
                task.completed_at,
            ))
            conn.commit()
            conn.close()

    def get_task(self, task_id: str) -> Optional[WorkspaceTask]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM workspace_tasks WHERE task_id = ?", (task_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return WorkspaceTask(
            task_id=row["task_id"],
            workspace_id=row["workspace_id"],
            type=row["type"],
            priority=TaskPriority(row["priority"]),
            status=TaskStatus(row["status"]),
            progress=json.loads(row["progress_json"] or "{}"),
            result_reference=row["result_reference"],
            error=json.loads(row["error_json"]) if row["error_json"] else None,
            idempotency_key=row["idempotency_key"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    def get_task_by_idempotency_key(self, key: str) -> Optional[WorkspaceTask]:
        if not key:
            return None
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM workspace_tasks WHERE idempotency_key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return WorkspaceTask(
            task_id=row["task_id"],
            workspace_id=row["workspace_id"],
            type=row["type"],
            priority=TaskPriority(row["priority"]),
            status=TaskStatus(row["status"]),
            progress=json.loads(row["progress_json"] or "{}"),
            result_reference=row["result_reference"],
            error=json.loads(row["error_json"]) if row["error_json"] else None,
            idempotency_key=row["idempotency_key"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )

    def list_tasks(
        self,
        workspace_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WorkspaceTask]:
        conn = self._get_connection()
        cur = conn.cursor()
        query = "SELECT * FROM workspace_tasks WHERE workspace_id = ?"
        params: List[Any] = [workspace_id]
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return [
            WorkspaceTask(
                task_id=row["task_id"],
                workspace_id=row["workspace_id"],
                type=row["type"],
                priority=TaskPriority(row["priority"]),
                status=TaskStatus(row["status"]),
                progress=json.loads(row["progress_json"] or "{}"),
                result_reference=row["result_reference"],
                error=json.loads(row["error_json"]) if row["error_json"] else None,
                idempotency_key=row["idempotency_key"],
                created_at=row["created_at"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
            )
            for row in rows
        ]

    # =========================================================================
    # Workspace Snapshots
    # =========================================================================

    def save_snapshot(self, snap: WorkspaceSnapshot) -> None:
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
            INSERT OR REPLACE INTO workspace_snapshots (
                snapshot_id, workspace_id, state_json, created_at
            ) VALUES (?, ?, ?, ?)
            """, (
                snap.snapshot_id,
                snap.workspace_id,
                json.dumps(snap.state or {}),
                snap.created_at,
            ))
            conn.commit()
            conn.close()

    def get_snapshot(self, snapshot_id: str) -> Optional[WorkspaceSnapshot]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM workspace_snapshots WHERE snapshot_id = ?", (snapshot_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return WorkspaceSnapshot(
            snapshot_id=row["snapshot_id"],
            workspace_id=row["workspace_id"],
            state=json.loads(row["state_json"] or "{}"),
            created_at=row["created_at"],
        )

    def list_snapshots(self, workspace_id: str) -> List[WorkspaceSnapshot]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM workspace_snapshots WHERE workspace_id = ? ORDER BY created_at DESC", (workspace_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            WorkspaceSnapshot(
                snapshot_id=row["snapshot_id"],
                workspace_id=row["workspace_id"],
                state=json.loads(row["state_json"] or "{}"),
                created_at=row["created_at"],
            )
            for row in rows
        ]
