"""
TRINETRA / Shanetra Geospatial Exploration Engine
AI Command Executor & State Patch Engine
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Executes validated commands sequentially with idempotency, partial failure isolation, and patch generation.
"""

from typing import Any, Dict, List, Optional, Tuple
from exploration.ai_schemas import (
    ExploreCommand,
    ExploreCommandPlan,
    CommandExecutionItem,
    CommandExecutionStatus,
    ExploreStatePatch,
    FlyToCommand,
    ZoomInCommand,
    ZoomOutCommand,
    ResetViewCommand,
    ShowLayerCommand,
    HideLayerCommand,
    SetOpacityCommand,
    RemoveLayerCommand,
    SearchDatasetsCommand,
    AddDatasetLayerCommand,
    SetAOICommand,
    ClearAOICommand,
    SetDateRangeCommand,
    SelectObservationCommand,
    CompareObservationsCommand,
    RunAnalysisCommand,
    FocusFindingCommand,
    ShowEvidenceCommand,
    RunInvestigationCommand,
    FocusEvidenceCommand,
    ShowTimelineCommand,
    TrackObjectCommand,
    CompareRegionsCommand,
    SearchIntelligenceCommand,
    OpenEventCommand,
    OpenFindingCommand,
    FindSimilarCommand,
    RunTemplateCommand,
    CreateMonitorCommand,
    ShowAnomaliesCommand,
    ShowHotspotsCommand,
    OpenWorkspaceCommand,
    CreateWorkspaceCommand,
    PinToEvidenceBoardCommand,
    RunInvestigationPlanCommand,
    ExportReportCommand,
    EXPLORE_COMMAND_FAILED,
    EXPLORE_LOCATION_AMBIGUOUS,
    EXPLORE_LOCATION_NOT_FOUND,
)

from exploration.geo_resolver import GeoResolver
from exploration.service import explore_service



class CommandExecutor:
    """Sequential executor producing atomic command items and state patch."""

    @classmethod
    def execute_plan(
        cls,
        plan: ExploreCommandPlan,
        current_active_layers: List[str],
        current_camera: Optional[Dict[str, Any]] = None,
        current_opacities: Optional[Dict[str, float]] = None,
    ) -> Tuple[str, List[CommandExecutionItem], ExploreStatePatch, Optional[str]]:
        """
        Executes an ExploreCommandPlan sequentially.
        Returns (overall_status, execution_items, state_patch, error_code).
        overall_status in ["completed", "partial_failure", "error"].
        """
        items: List[CommandExecutionItem] = []
        active_layers = list(current_active_layers)
        opacities = dict(current_opacities or {})
        camera_patch = None
        dataset_id_patch = None
        aoi_patch = None
        date_range_patch = None
        selected_obs_patch = None
        comparison_patch = None
        has_failure = False
        error_code = None

        for idx, cmd in enumerate(plan.commands):
            cmd_id = f"cmd_{idx + 1:03d}"
            cmd_type = getattr(cmd, "type", "UNKNOWN")

            if has_failure:
                items.append(
                    CommandExecutionItem(
                        command_id=cmd_id,
                        type=cmd_type,
                        status=CommandExecutionStatus.CANCELLED,
                        message="Cancelled due to prior command failure in plan.",
                    )
                )
                continue

            # Execute individual command
            status, msg, details, err = cls._execute_single_command(
                cmd, active_layers, opacities, current_camera
            )

            if status == CommandExecutionStatus.FAILED:
                has_failure = True
                error_code = err or EXPLORE_COMMAND_FAILED

            # Capture patches
            if details.get("camera"):
                camera_patch = details["camera"]
            if details.get("dataset_id"):
                dataset_id_patch = details["dataset_id"]
            if "aoi" in details:
                aoi_patch = details["aoi"]
            if "date_range" in details:
                date_range_patch = details["date_range"]
            if "selected_observation_id" in details:
                selected_obs_patch = details["selected_observation_id"]
            if "comparison" in details:
                comparison_patch = details["comparison"]
            if "active_finding_id" in details:
                active_finding_patch = details["active_finding_id"]
            if "analysis" in details:
                analysis_patch = details["analysis"]
            if "investigation" in details:
                investigation_patch = details["investigation"]
            if "focused_evidence_id" in details:
                focused_evidence_patch = details["focused_evidence_id"]
            if "timeline_active" in details:
                timeline_active_patch = details["timeline_active"]
            if "object_tracking" in details:
                object_tracking_patch = details["object_tracking"]
            if "active_event_id" in details:
                active_event_patch = details["active_event_id"]
            if "intelligence_search" in details:
                intelligence_search_patch = details["intelligence_search"]
            if "intelligence_tab" in details:
                intelligence_tab_patch = details["intelligence_tab"]
            if "active_monitor_id" in details:
                active_monitor_patch = details["active_monitor_id"]
            if "anomalies_active" in details:
                anomalies_active_patch = details["anomalies_active"]
            if "hotspots_active" in details:
                hotspots_active_patch = details["hotspots_active"]
            if "active_workspace_id" in details:
                active_workspace_id_patch = details["active_workspace_id"]
            if "active_workspace_tab" in details:
                active_workspace_tab_patch = details["active_workspace_tab"]
            if "evidence_board_active" in details:
                evidence_board_active_patch = details["evidence_board_active"]
            if "active_plan_id" in details:
                active_plan_id_patch = details["active_plan_id"]

            items.append(
                CommandExecutionItem(
                    command_id=cmd_id,
                    type=cmd_type,
                    status=status,
                    message=msg,
                    details=details,
                )
            )

        overall_status = "completed"
        if has_failure:
            overall_status = "partial_failure" if any(i.status == CommandExecutionStatus.EXECUTED for i in items) else "error"

        patch = ExploreStatePatch(
            camera=camera_patch,
            visible_layer_ids=active_layers,
            layer_opacities=opacities,
            active_dataset_id=dataset_id_patch,
            aoi=aoi_patch,
            date_range=date_range_patch,
            selected_observation_id=selected_obs_patch,
            comparison=comparison_patch,
            active_finding_id=active_finding_patch if "active_finding_patch" in locals() else None,
            analysis=analysis_patch if "analysis_patch" in locals() else None,
            investigation=investigation_patch if "investigation_patch" in locals() else None,
            focused_evidence_id=focused_evidence_patch if "focused_evidence_patch" in locals() else None,
            timeline_active=timeline_active_patch if "timeline_active_patch" in locals() else None,
            object_tracking=object_tracking_patch if "object_tracking_patch" in locals() else None,
            active_event_id=active_event_patch if "active_event_patch" in locals() else None,
            intelligence_search=intelligence_search_patch if "intelligence_search_patch" in locals() else None,
            intelligence_tab=intelligence_tab_patch if "intelligence_tab_patch" in locals() else None,
            active_monitor_id=active_monitor_patch if "active_monitor_patch" in locals() else None,
            anomalies_active=anomalies_active_patch if "anomalies_active_patch" in locals() else None,
            hotspots_active=hotspots_active_patch if "hotspots_active_patch" in locals() else None,
            active_workspace_id=active_workspace_id_patch if "active_workspace_id_patch" in locals() else None,
            active_workspace_tab=active_workspace_tab_patch if "active_workspace_tab_patch" in locals() else None,
            evidence_board_active=evidence_board_active_patch if "evidence_board_active_patch" in locals() else None,
            active_plan_id=active_plan_id_patch if "active_plan_id_patch" in locals() else None,
        )


        return overall_status, items, patch, error_code


    @classmethod
    def _execute_single_command(
        cls,
        cmd: ExploreCommand,
        active_layers: List[str],
        opacities: Dict[str, float],
        current_camera: Optional[Dict[str, Any]],
    ) -> Tuple[CommandExecutionStatus, str, Dict[str, Any], Optional[str]]:
        cmd_type = cmd.type

        # 1. FLY_TO
        if isinstance(cmd, FlyToCommand):
            lat = cmd.latitude
            lon = cmd.longitude
            zoom = cmd.zoom or 10.0
            name = cmd.location_query or "Target location"

            if lat is None or lon is None:
                if not cmd.location_query:
                    return CommandExecutionStatus.FAILED, "Missing coordinates or location query", {}, EXPLORE_COMMAND_FAILED

                target = GeoResolver.resolve(cmd.location_query)
                if not target:
                    return CommandExecutionStatus.FAILED, f"Could not find coordinates for '{cmd.location_query}'.", {}, EXPLORE_LOCATION_NOT_FOUND

                if target.is_ambiguous:
                    cand_str = ", ".join(target.candidates[:3])
                    return (
                        CommandExecutionStatus.FAILED,
                        f"Location '{cmd.location_query}' is ambiguous ({cand_str}).",
                        {},
                        EXPLORE_LOCATION_AMBIGUOUS,
                    )

                lat = target.latitude
                lon = target.longitude
                name = target.name

            cam = {
                "latitude": lat,
                "longitude": lon,
                "zoom": zoom,
                "heading": cmd.heading or 0.0,
                "pitch": cmd.pitch or 0.0,
                "duration": cmd.duration or 1.5,
            }
            return CommandExecutionStatus.EXECUTED, f"Centered map on {name}.", {"camera": cam}, None

        # 2. ZOOM_IN
        elif isinstance(cmd, ZoomInCommand):
            current_zoom = (current_camera.get("zoom", 5.0) if current_camera else 5.0) + cmd.step
            cam = {"zoom": min(24.0, current_zoom)}
            return CommandExecutionStatus.EXECUTED, f"Zoomed in by {cmd.step} steps.", {"camera": cam}, None

        # 3. ZOOM_OUT
        elif isinstance(cmd, ZoomOutCommand):
            current_zoom = (current_camera.get("zoom", 5.0) if current_camera else 5.0) - cmd.step
            cam = {"zoom": max(0.0, current_zoom)}
            return CommandExecutionStatus.EXECUTED, f"Zoomed out by {cmd.step} steps.", {"camera": cam}, None

        # 4. RESET_VIEW
        elif isinstance(cmd, ResetViewCommand):
            cam = {"latitude": 20.5937, "longitude": 78.9629, "zoom": 4.5, "heading": 0.0, "pitch": 0.0}
            return CommandExecutionStatus.EXECUTED, "Reset Shanetra camera to overview.", {"camera": cam}, None

        # 5. SHOW_LAYER (Idempotent)
        elif isinstance(cmd, ShowLayerCommand):
            layer = explore_service.get_layer(cmd.layer_id)
            if not layer:
                return CommandExecutionStatus.FAILED, f"Layer '{cmd.layer_id}' not found.", {}, EXPLORE_COMMAND_FAILED

            if cmd.layer_id in active_layers:
                return CommandExecutionStatus.NO_OP, f"Layer '{layer.name}' is already active.", {}, None

            active_layers.append(cmd.layer_id)
            return CommandExecutionStatus.EXECUTED, f"Enabled layer '{layer.name}'.", {}, None

        # 6. HIDE_LAYER (Idempotent)
        elif isinstance(cmd, HideLayerCommand):
            layer = explore_service.get_layer(cmd.layer_id)
            layer_name = layer.name if layer else cmd.layer_id

            if cmd.layer_id not in active_layers:
                return CommandExecutionStatus.NO_OP, f"Layer '{layer_name}' is already hidden.", {}, None

            active_layers.remove(cmd.layer_id)
            return CommandExecutionStatus.EXECUTED, f"Hidden layer '{layer_name}'.", {}, None

        # 7. SET_LAYER_OPACITY
        elif isinstance(cmd, SetOpacityCommand):
            layer = explore_service.get_layer(cmd.layer_id)
            layer_name = layer.name if layer else cmd.layer_id
            opacities[cmd.layer_id] = cmd.opacity
            return (
                CommandExecutionStatus.EXECUTED,
                f"Set opacity for '{layer_name}' to {int(cmd.opacity * 100)}%.",
                {},
                None,
            )

        # 8. REMOVE_LAYER
        elif isinstance(cmd, RemoveLayerCommand):
            if cmd.layer_id in active_layers:
                active_layers.remove(cmd.layer_id)
            return CommandExecutionStatus.EXECUTED, f"Removed layer '{cmd.layer_id}'.", {}, None

        # 9. SEARCH_DATASETS
        elif isinstance(cmd, SearchDatasetsCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Queried Earth Observation catalog for '{cmd.collection or cmd.query or 'satellite data'}'.",
                {"search_query": cmd.query, "collection": cmd.collection},
                None,
            )

        # 10. ADD_DATASET_LAYER
        elif isinstance(cmd, AddDatasetLayerCommand):
            layer = explore_service.register_dataset_layer(cmd.asset_id, cmd.title)
            if not layer:
                return CommandExecutionStatus.FAILED, f"Failed to promote asset '{cmd.asset_id}' to layer.", {}, EXPLORE_COMMAND_FAILED

            if layer.id not in active_layers:
                active_layers.append(layer.id)
            return CommandExecutionStatus.EXECUTED, f"Added satellite layer '{layer.name}'.", {"dataset_id": cmd.asset_id}, None

        # 11. SET_AOI
        elif isinstance(cmd, SetAOICommand):
            geom = cmd.geometry
            if not geom and cmd.bbox:
                min_lon, min_lat, max_lon, max_lat = cmd.bbox
                geom = {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [min_lon, min_lat],
                            [max_lon, min_lat],
                            [max_lon, max_lat],
                            [min_lon, max_lat],
                            [min_lon, min_lat],
                        ]
                    ],
                }
            return CommandExecutionStatus.EXECUTED, "Set Area of Interest boundary.", {"aoi": geom}, None

        # 12. CLEAR_AOI
        elif isinstance(cmd, ClearAOICommand):
            return CommandExecutionStatus.EXECUTED, "Cleared Area of Interest boundary.", {"aoi": None}, None

        # 13. SET_DATE_RANGE
        elif isinstance(cmd, SetDateRangeCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Set observation date filter to {cmd.start_date} – {cmd.end_date}.",
                {"date_range": {"start": cmd.start_date, "end": cmd.end_date}},
                None,
            )

        # 14. SELECT_OBSERVATION
        elif isinstance(cmd, SelectObservationCommand):
            obs = explore_service.get_observation(cmd.observation_id)
            title = obs.id if obs else cmd.observation_id
            return (
                CommandExecutionStatus.EXECUTED,
                f"Selected observation '{title}'.",
                {"selected_observation_id": cmd.observation_id, "target_slot": cmd.target_slot},
                None,
            )

        # 15. COMPARE_OBSERVATIONS
        elif isinstance(cmd, CompareObservationsCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Activated {cmd.mode} comparison between '{cmd.observation_a_id}' and '{cmd.observation_b_id}'.",
                {
                    "comparison": {
                        "observation_a_id": cmd.observation_a_id,
                        "observation_b_id": cmd.observation_b_id,
                        "mode": cmd.mode,
                    }
                },
                None,
            )

        # 16. RUN_ANALYSIS
        elif isinstance(cmd, RunAnalysisCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Triggered {cmd.mode} Earth Observation analysis.",
                {
                    "analysis": {
                        "mode": cmd.mode,
                        "query": cmd.query,
                        "trigger": True,
                    }
                },
                None,
            )

        # 17. FOCUS_FINDING
        elif isinstance(cmd, FocusFindingCommand):
            details: Dict[str, Any] = {"active_finding_id": cmd.finding_id}
            if cmd.latitude is not None and cmd.longitude is not None:
                details["camera"] = {
                    "latitude": cmd.latitude,
                    "longitude": cmd.longitude,
                    "zoom": cmd.zoom or 14.0,
                }
            return (
                CommandExecutionStatus.EXECUTED,
                f"Focused finding '{cmd.finding_id}'.",
                details,
                None,
            )

        # 18. SHOW_EVIDENCE
        elif isinstance(cmd, ShowEvidenceCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Highlighted evidence item '{cmd.evidence_id}'.",
                {"active_evidence_id": cmd.evidence_id},
                None,
            )

        # 19. RUN_INVESTIGATION
        elif isinstance(cmd, RunInvestigationCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Enqueued investigation: '{cmd.question}'.",
                {"investigation": {"question": cmd.question, "observation_ids": cmd.observation_ids, "status": "queued"}},
                None,
            )

        # 20. FOCUS_EVIDENCE
        elif isinstance(cmd, FocusEvidenceCommand):
            details = {"focused_evidence_id": cmd.evidence_id}
            if cmd.latitude is not None and cmd.longitude is not None:
                details["camera"] = {"latitude": cmd.latitude, "longitude": cmd.longitude, "zoom": cmd.zoom or 15.0}
            return (
                CommandExecutionStatus.EXECUTED,
                f"Focused evidence item '{cmd.evidence_id}'.",
                details,
                None,
            )

        # 21. SHOW_TIMELINE
        elif isinstance(cmd, ShowTimelineCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                "Opened multi-temporal investigation timeline.",
                {"timeline_active": True, "investigation_id": cmd.investigation_id},
                None,
            )

        # 22. TRACK_OBJECT
        elif isinstance(cmd, TrackObjectCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Tracking object class '{cmd.target_class}'.",
                {"object_tracking": {"target_class": cmd.target_class, "observation_ids": cmd.observation_ids}},
                None,
            )

        # 23. COMPARE_REGIONS
        elif isinstance(cmd, CompareRegionsCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Comparing regions '{cmd.region_a_id}' and '{cmd.region_b_id}'.",
                {"comparison": {"region_a": cmd.region_a_id, "region_b": cmd.region_b_id}},
                None,
            )

        # 24. SEARCH_INTELLIGENCE
        elif isinstance(cmd, SearchIntelligenceCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Executing intelligence search for '{cmd.query}'.",
                {
                    "intelligence_search": {
                        "query": cmd.query,
                        "semantic_class": cmd.semantic_class,
                        "state": cmd.state,
                        "min_confidence": cmd.min_confidence,
                    },
                    "intelligence_tab": "search",
                },
                None,
            )

        # 25. OPEN_EVENT
        elif isinstance(cmd, OpenEventCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Opened EO Event '{cmd.event_id}'.",
                {"active_event_id": cmd.event_id, "intelligence_tab": "events"},
                None,
            )

        # 26. OPEN_FINDING
        elif isinstance(cmd, OpenFindingCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Opened persistent finding '{cmd.finding_id}'.",
                {"active_finding_id": cmd.finding_id, "intelligence_tab": "findings"},
                None,
            )

        # 27. FIND_SIMILAR
        elif isinstance(cmd, FindSimilarCommand):
            target = cmd.event_id or cmd.finding_id
            return (
                CommandExecutionStatus.EXECUTED,
                f"Finding similar events and findings to '{target}'.",
                {
                    "intelligence_search": {
                        "event_id": cmd.event_id,
                        "finding_id": cmd.finding_id,
                        "type": "similarity",
                    },
                    "intelligence_tab": "similarity",
                },
                None,
            )

        # 28. RUN_TEMPLATE
        elif isinstance(cmd, RunTemplateCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Triggered investigation template '{cmd.template_id}'.",
                {
                    "investigation": {
                        "template_id": cmd.template_id,
                        "region_id": cmd.region_id,
                        "status": "queued",
                    },
                    "intelligence_tab": "templates",
                },
                None,
            )

        # 29. CREATE_MONITOR
        elif isinstance(cmd, CreateMonitorCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Configured persistent monitor '{cmd.name}'.",
                {
                    "active_monitor_id": cmd.name,
                    "intelligence_tab": "monitoring",
                },
                None,
            )

        # 30. SHOW_ANOMALIES
        elif isinstance(cmd, ShowAnomaliesCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                "Displaying regional anomalies panel.",
                {
                    "anomalies_active": True,
                    "intelligence_tab": "anomalies",
                },
                None,
            )

        # 31. SHOW_HOTSPOTS
        elif isinstance(cmd, ShowHotspotsCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                "Displaying spatial activity hotspots.",
                {
                    "hotspots_active": True,
                    "intelligence_tab": "hotspots",
                },
                None,
            )

        # 32. OPEN_WORKSPACE
        elif isinstance(cmd, OpenWorkspaceCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Opened analyst workspace '{cmd.workspace_id}'.",
                {
                    "active_workspace_id": cmd.workspace_id,
                    "active_workspace_tab": cmd.tab or "overview",
                },
                None,
            )

        # 33. CREATE_WORKSPACE
        elif isinstance(cmd, CreateWorkspaceCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Created analyst workspace '{cmd.name}'.",
                {
                    "active_workspace_id": f"ws-{cmd.name.lower().replace(' ', '-')[:16]}",
                    "active_workspace_tab": "overview",
                },
                None,
            )

        # 34. PIN_TO_BOARD
        elif isinstance(cmd, PinToEvidenceBoardCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Pinned {cmd.item_type} '{cmd.source_id}' to evidence board.",
                {
                    "evidence_board_active": True,
                    "active_workspace_tab": "board",
                },
                None,
            )

        # 35. RUN_INVESTIGATION_PLAN
        elif isinstance(cmd, RunInvestigationPlanCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Dispatched execution for investigation plan '{cmd.plan_id}'.",
                {
                    "active_plan_id": cmd.plan_id,
                    "active_workspace_tab": "plans",
                },
                None,
            )

        # 36. EXPORT_REPORT
        elif isinstance(cmd, ExportReportCommand):
            return (
                CommandExecutionStatus.EXECUTED,
                f"Generated export package for report '{cmd.report_id}'.",
                {
                    "active_workspace_tab": "reports",
                },
                None,
            )

        return CommandExecutionStatus.FAILED, f"Unexecutable command type '{cmd_type}'.", {}, EXPLORE_COMMAND_FAILED



    @classmethod
    def generate_user_summary(cls, items: List[CommandExecutionItem]) -> str:
        """Deterministically generates clean user explanation without calling an LLM."""
        executed = [i for i in items if i.status == CommandExecutionStatus.EXECUTED]
        if not executed:
            no_ops = [i for i in items if i.status == CommandExecutionStatus.NO_OP]
            if no_ops:
                return "No changes needed; requested layers are already active."
            return "Unable to execute requested map operations."

        messages = [i.message for i in executed]
        return " ".join(messages)
