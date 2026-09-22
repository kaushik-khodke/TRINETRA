"""
TRINETRA Phase 8 — Central Analyst Workspace Service
Coordinates all workspace subsystems: lifecycle, operational context, DAG planning,
multi-region comparison, batch processing, evidence boards, reviews, reporting, and tasks.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from backend.workspace.models import (
        Workspace,
        WorkspaceStatus,
        WorkspaceContext,
        WorkspaceActivity,
        InvestigationPlan,
        InvestigationStep,
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
        ReportDocument,
        ReportSection,
        ReportStatus,
        WorkspaceTask,
        TaskPriority,
        TaskStatus,
        WorkspaceSnapshot,
    )
    from backend.workspace.repository import WorkspaceRepository
    from backend.workspace.lifecycle import WorkspaceLifecycleManager
    from backend.workspace.context import WorkspaceContextManager
    from backend.workspace.activity import WorkspaceActivityTracker
    from backend.workspace.planning.planner import InvestigationPlanner
    from backend.workspace.comparison.regions import RegionComparator
    from backend.workspace.comparison.events import EventComparator
    from backend.workspace.comparison.findings import FindingComparator
    from backend.workspace.batch.executor import BatchExecutor
    from backend.workspace.synthesis.builder import WorkspaceSynthesizer
    from backend.workspace.annotations.service import AnnotationService
    from backend.workspace.reports.builder import ReportBuilder
    from backend.workspace.reports.exporter import ReportPackageExporter
    from backend.workspace.reports.renderer import ReportPresentationRenderer
    from backend.workspace.task_queue.service import WorkspaceTaskService
except ImportError:
    from workspace.models import (
        Workspace,
        WorkspaceStatus,
        WorkspaceContext,
        WorkspaceActivity,
        InvestigationPlan,
        InvestigationStep,
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
        ReportDocument,
        ReportSection,
        ReportStatus,
        WorkspaceTask,
        TaskPriority,
        TaskStatus,
        WorkspaceSnapshot,
    )
    from workspace.repository import WorkspaceRepository
    from workspace.lifecycle import WorkspaceLifecycleManager
    from workspace.context import WorkspaceContextManager
    from workspace.activity import WorkspaceActivityTracker
    from workspace.planning.planner import InvestigationPlanner
    from workspace.comparison.regions import RegionComparator
    from workspace.comparison.events import EventComparator
    from workspace.comparison.findings import FindingComparator
    from workspace.batch.executor import BatchExecutor
    from workspace.synthesis.builder import WorkspaceSynthesizer
    from workspace.annotations.service import AnnotationService
    from workspace.reports.builder import ReportBuilder
    from workspace.reports.exporter import ReportPackageExporter
    from workspace.reports.renderer import ReportPresentationRenderer
    from workspace.task_queue.service import WorkspaceTaskService


class WorkspaceService:
    """
    Unified entry point for TRINETRA Analyst Command Center workflows.
    """

    def __init__(
        self,
        repository: Optional[WorkspaceRepository] = None,
        intelligence_service=None,
    ):
        self.repo = repository or WorkspaceRepository()
        self.intelligence_service = intelligence_service
        self.activity_tracker = WorkspaceActivityTracker(self.repo)

        self.planner = InvestigationPlanner(self.repo, self.activity_tracker, self.intelligence_service)
        self.region_comparator = RegionComparator(self.repo, self.activity_tracker, self.intelligence_service)
        self.event_comparator = EventComparator(self.repo, self.intelligence_service)
        self.finding_comparator = FindingComparator(self.repo, self.intelligence_service)
        self.batch_executor = BatchExecutor(self.repo, self.activity_tracker)
        self.synthesizer = WorkspaceSynthesizer(self.repo, self.activity_tracker)
        self.annotation_service = AnnotationService(self.repo, self.activity_tracker)
        self.report_builder = ReportBuilder(self.repo, self.activity_tracker)
        self.task_service = WorkspaceTaskService(self.repo, self.activity_tracker)

    # =========================================================================
    # Workspace Core Lifecycle & Management
    # =========================================================================

    def create_workspace(
        self,
        name: str,
        description: str = "",
        current_aoi: Optional[Dict[str, Any]] = None,
        created_by: str = "analyst",
    ) -> Workspace:
        ws_id = f"ws-{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        ws = Workspace(
            workspace_id=ws_id,
            name=name,
            description=description,
            status=WorkspaceStatus.CREATED,
            current_aoi=current_aoi or {},
            created_at=now_str,
            updated_at=now_str,
            created_by=created_by,
        )
        self.repo.save_workspace(ws)

        # Initialize lightweight operational context
        init_ctx = WorkspaceContextManager.create_initial_context(ws_id, current_aoi)
        self.repo.save_context(init_ctx)

        self.activity_tracker.log(
            workspace_id=ws_id,
            activity_type="WORKSPACE_CREATED",
            entity_type="WORKSPACE",
            entity_id=ws_id,
            details={"name": name},
            actor=created_by,
        )

        return ws

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        return self.repo.get_workspace(workspace_id)

    def list_workspaces(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Workspace]:
        return self.repo.list_workspaces(status=status, limit=limit, offset=offset)

    def update_workspace(
        self,
        workspace_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        current_aoi: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
    ) -> Workspace:
        ws = self.repo.get_workspace(workspace_id)
        if not ws:
            raise ValueError(f"Workspace '{workspace_id}' not found.")

        if name is not None:
            ws.name = name
        if description is not None:
            ws.description = description
        if current_aoi is not None:
            ws.current_aoi = current_aoi

        if status is not None:
            target_status = WorkspaceStatus(status)
            WorkspaceLifecycleManager.validate_transition(ws.status, target_status)
            ws.status = target_status

        ws.updated_at = datetime.now(timezone.utc).isoformat()
        self.repo.save_workspace(ws)

        self.activity_tracker.log(
            workspace_id=workspace_id,
            activity_type="WORKSPACE_UPDATED",
            entity_type="WORKSPACE",
            entity_id=workspace_id,
            details={"status": ws.status.value},
        )

        return ws

    def delete_workspace(self, workspace_id: str) -> bool:
        return self.repo.delete_workspace(workspace_id)

    # =========================================================================
    # Operational Context
    # =========================================================================

    def get_context(self, workspace_id: str) -> Optional[WorkspaceContext]:
        ctx = self.repo.get_context(workspace_id)
        if not ctx:
            ws = self.repo.get_workspace(workspace_id)
            if ws:
                ctx = WorkspaceContextManager.create_initial_context(workspace_id, ws.current_aoi)
                self.repo.save_context(ctx)
        return ctx

    def update_context(
        self,
        workspace_id: str,
        aoi: Optional[Dict[str, Any]] = None,
        region_ids: Optional[List[str]] = None,
        observation_ids: Optional[List[str]] = None,
        event_ids: Optional[List[str]] = None,
        finding_ids: Optional[List[str]] = None,
        open_investigation_id: Optional[str] = None,
        active_comparison_id: Optional[str] = None,
        active_report_id: Optional[str] = None,
    ) -> WorkspaceContext:
        ctx = self.get_context(workspace_id)
        if not ctx:
            raise ValueError(f"Workspace '{workspace_id}' not found.")

        updated = WorkspaceContextManager.patch_context(
            current=ctx,
            current_aoi=aoi,
            active_regions=region_ids,
            selected_observations=observation_ids,
            selected_events=event_ids,
            selected_findings=finding_ids,
            open_investigation_id=open_investigation_id,
            active_comparison_id=active_comparison_id,
            active_report_id=active_report_id,
        )
        self.repo.save_context(updated)
        return updated

    # =========================================================================
    # Evidence Board Operations
    # =========================================================================

    def pin_item(
        self,
        workspace_id: str,
        item_type: str,
        source_id: str,
        position: Optional[Dict[str, float]] = None,
        title: str = "",
        annotation: str = "",
    ) -> EvidenceBoardItem:
        items = self.repo.list_board_items(workspace_id)
        # Prevent exact duplicate pin
        for existing in items:
            if existing.type == item_type and existing.source_id == source_id:
                return existing

        item = EvidenceBoardItem(
            item_id=f"item-{uuid.uuid4().hex[:12]}",
            workspace_id=workspace_id,
            type=item_type,
            source_id=source_id,
            position=position or {"x": 120.0 + len(items) * 30.0, "y": 100.0 + (len(items) % 5) * 40.0},
            title=title or f"{item_type} {source_id}",
            annotation=annotation,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.repo.save_board_item(item)

        self.activity_tracker.log(
            workspace_id=workspace_id,
            activity_type="ITEM_PINNED",
            entity_type=item_type,
            entity_id=source_id,
            details={"item_id": item.item_id, "title": item.title},
        )

        return item

    def list_board_items(self, workspace_id: str) -> List[EvidenceBoardItem]:
        return self.repo.list_board_items(workspace_id)

    def delete_board_item(self, item_id: str) -> bool:
        return self.repo.delete_board_item(item_id)

    def link_items(
        self,
        workspace_id: str,
        source_item_id: str,
        target_item_id: str,
        relation_type: str = "supports",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceBoardRelation:
        rel = EvidenceBoardRelation(
            relation_id=f"rel-{uuid.uuid4().hex[:12]}",
            workspace_id=workspace_id,
            source_item_id=source_item_id,
            target_item_id=target_item_id,
            relation_type=relation_type,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.repo.save_board_relation(rel)

        self.activity_tracker.log(
            workspace_id=workspace_id,
            activity_type="ITEMS_LINKED",
            entity_type="RELATION",
            entity_id=rel.relation_id,
            details={"source": source_item_id, "target": target_item_id, "type": relation_type},
        )

        return rel

    def list_board_relations(self, workspace_id: str) -> List[EvidenceBoardRelation]:
        return self.repo.list_board_relations(workspace_id)

    def delete_board_relation(self, relation_id: str) -> bool:
        return self.repo.delete_board_relation(relation_id)

    # =========================================================================
    # Investigation Plans & DAG Execution
    # =========================================================================

    def create_plan(
        self,
        workspace_id: str,
        title: str,
        question: str,
        steps: Optional[List[InvestigationStep]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        required_evidence: Optional[List[str]] = None,
    ) -> InvestigationPlan:
        return self.planner.create_plan(
            workspace_id=workspace_id,
            title=title,
            question=question,
            steps=steps,
            constraints=constraints,
            required_evidence=required_evidence,
        )

    def get_plan(self, plan_id: str) -> Optional[InvestigationPlan]:
        return self.repo.get_plan(plan_id)

    def list_plans(self, workspace_id: str) -> List[InvestigationPlan]:
        return self.repo.list_plans(workspace_id)

    def execute_plan(
        self,
        plan_id: str,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> InvestigationPlanRun:
        return self.planner.execute_plan(plan_id, execution_context)

    def list_plan_runs(self, plan_id: str) -> List[InvestigationPlanRun]:
        return self.repo.list_plan_runs(plan_id)

    # =========================================================================
    # Comparison & Sensitivity Analysis
    # =========================================================================

    def compare_regions(
        self,
        workspace_id: str,
        region_a_id: str,
        region_b_id: str,
        period: str = "last_12_months",
        thresholds: Optional[List[float]] = None,
    ) -> RegionComparison:
        return self.region_comparator.compare_regions(
            workspace_id=workspace_id,
            region_a_id=region_a_id,
            region_b_id=region_b_id,
            period=period,
            thresholds=thresholds,
        )

    def list_comparisons(self, workspace_id: str) -> List[RegionComparison]:
        return self.repo.list_comparisons(workspace_id)

    def compare_events(self, workspace_id: str, event_ids: List[str]) -> Dict[str, Any]:
        return self.event_comparator.compare_events(workspace_id, event_ids)

    def compare_findings(self, finding_ids: List[str]) -> Dict[str, Any]:
        return self.finding_comparator.compare_findings(finding_ids)

    # =========================================================================
    # Batch Processing
    # =========================================================================

    def execute_batch(
        self,
        workspace_id: str,
        template_id: str,
        targets: List[Dict[str, Any]],
        concurrency: int = 2,
    ) -> BatchJob:
        return self.batch_executor.execute_batch(
            workspace_id=workspace_id,
            template_id=template_id,
            targets=targets,
            concurrency=concurrency,
        )

    def get_batch_job(self, batch_id: str) -> Optional[BatchJob]:
        return self.repo.get_batch_job(batch_id)

    def list_batch_jobs(self, workspace_id: str) -> List[BatchJob]:
        return self.repo.list_batch_jobs(workspace_id)

    # =========================================================================
    # Synthesis & Conflict Detection
    # =========================================================================

    def generate_synthesis(self, workspace_id: str) -> Dict[str, Any]:
        return self.synthesizer.synthesize(workspace_id)

    # =========================================================================
    # Annotations, Reviews & Follow-ups
    # =========================================================================

    def add_annotation(
        self,
        workspace_id: str,
        text: str,
        type: str = "TEXT",
        geometry: Optional[Dict[str, Any]] = None,
        linked_entity_type: Optional[str] = None,
        linked_entity_id: Optional[str] = None,
    ) -> Annotation:
        return self.annotation_service.add_annotation(
            workspace_id=workspace_id,
            text=text,
            type=type,
            geometry=geometry,
            linked_entity_type=linked_entity_type,
            linked_entity_id=linked_entity_id,
        )

    def list_annotations(self, workspace_id: str) -> List[Annotation]:
        return self.repo.list_annotations(workspace_id)

    def delete_annotation(self, annotation_id: str) -> bool:
        return self.repo.delete_annotation(annotation_id)

    def set_review_status(
        self,
        workspace_id: str,
        entity_type: str,
        entity_id: str,
        status: ReviewStatus,
        review_note: str = "",
        analyst_id: str = "analyst",
    ) -> ReviewRecord:
        return self.annotation_service.set_review_status(
            workspace_id=workspace_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            review_note=review_note,
            analyst_id=analyst_id,
        )

    def list_reviews(self, workspace_id: str) -> List[ReviewRecord]:
        return self.repo.list_reviews(workspace_id)

    def create_follow_up(
        self,
        workspace_id: str,
        linked_entity_type: str,
        linked_entity_id: str,
        note: str,
        status: str = "OPEN",
    ) -> FollowUp:
        return self.annotation_service.create_follow_up(
            workspace_id=workspace_id,
            linked_entity_type=linked_entity_type,
            linked_entity_id=linked_entity_id,
            note=note,
            status=status,
        )

    def list_follow_ups(self, workspace_id: str, status: Optional[str] = None) -> List[FollowUp]:
        return self.repo.list_follow_ups(workspace_id, status=status)

    # =========================================================================
    # Reporting & Dossier Export
    # =========================================================================

    def create_report(
        self,
        workspace_id: str,
        title: str,
        sections: List[ReportSection],
        strict_claims: bool = True,
    ) -> ReportDocument:
        return self.report_builder.create_report(
            workspace_id=workspace_id,
            title=title,
            sections=sections,
            strict_claims=strict_claims,
        )

    def get_report(self, report_id: str) -> Optional[ReportDocument]:
        return self.repo.get_report(report_id)

    def list_reports(self, workspace_id: str) -> List[ReportDocument]:
        return self.repo.list_reports(workspace_id)

    def render_report_html(self, report_id: str) -> str:
        report = self.repo.get_report(report_id)
        if not report:
            raise ValueError(f"Report '{report_id}' not found.")
        ws = self.repo.get_workspace(report.workspace_id)
        aoi = ws.current_aoi if ws else {}
        return ReportPresentationRenderer.render_html(report, aoi_geojson=aoi)

    def export_report_package(self, report_id: str, output_dir: Optional[str] = None) -> str:
        report = self.repo.get_report(report_id)
        if not report:
            raise ValueError(f"Report '{report_id}' not found.")
        ws = self.repo.get_workspace(report.workspace_id)
        aoi = ws.current_aoi if ws else {}
        return ReportPackageExporter.export_zip(report, output_dir=output_dir, aoi_geojson=aoi)

    # =========================================================================
    # Task Queue Operations
    # =========================================================================

    def submit_task(
        self,
        workspace_id: str,
        type: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        parameters: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> WorkspaceTask:
        return self.task_service.submit_task(
            workspace_id=workspace_id,
            type=type,
            priority=priority,
            parameters=parameters,
            idempotency_key=idempotency_key,
        )

    def get_task(self, task_id: str) -> Optional[WorkspaceTask]:
        return self.repo.get_task(task_id)

    def list_tasks(
        self,
        workspace_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[WorkspaceTask]:
        return self.repo.list_tasks(workspace_id, status=status, limit=limit, offset=offset)

    def cancel_task(self, task_id: str) -> bool:
        return self.task_service.cancel_task(task_id)

    # =========================================================================
    # Activity Audit Log
    # =========================================================================

    def list_activities(
        self,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0,
        activity_type: Optional[str] = None,
        entity_type: Optional[str] = None,
    ) -> List[WorkspaceActivity]:
        return self.activity_tracker.list_activities(
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
            activity_type=activity_type,
            entity_type=entity_type,
        )

    # =========================================================================
    # Snapshots
    # =========================================================================

    def create_snapshot(
        self,
        workspace_id: str,
        state: Optional[Dict[str, Any]] = None,
    ) -> WorkspaceSnapshot:
        snapshot_id = f"snap-{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        if state is None:
            # Automatic snapshot of workspace context & board items
            ctx = self.get_context(workspace_id)
            items = self.list_board_items(workspace_id)
            relations = self.list_board_relations(workspace_id)
            state = {
                "context": ctx.to_dict() if ctx else {},
                "board_items": [i.to_dict() for i in items],
                "board_relations": [r.to_dict() for r in relations],
            }

        snap = WorkspaceSnapshot(
            snapshot_id=snapshot_id,
            workspace_id=workspace_id,
            state=state,
            created_at=now_str,
        )
        self.repo.save_snapshot(snap)

        self.activity_tracker.log(
            workspace_id=workspace_id,
            activity_type="SNAPSHOT_CREATED",
            entity_type="SNAPSHOT",
            entity_id=snapshot_id,
        )

        return snap

    def get_snapshot(self, snapshot_id: str) -> Optional[WorkspaceSnapshot]:
        return self.repo.get_snapshot(snapshot_id)

    def list_snapshots(self, workspace_id: str) -> List[WorkspaceSnapshot]:
        return self.repo.list_snapshots(workspace_id)
