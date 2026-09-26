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
                if camera_patch is None:
                    camera_patch = {}
                camera_patch.update(details["camera"])
                if current_camera is None:
                    current_camera = {}
                current_camera.update(details["camera"])
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
            zoom = cmd.zoom or 11.5
            name = cmd.location_query or "Target location"
            bbox = None

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
                bbox = getattr(target, "bbox", None)
                if getattr(target, "zoom", None):
                    zoom = target.zoom
                elif bbox:
                    from exploration.fallback_parser import FallbackParser
                    zoom = FallbackParser.calculate_zoom(bbox, default=11.5)
            else:
                if cmd.location_query:
                    target = GeoResolver.resolve(cmd.location_query)
                    if target and getattr(target, "bbox", None):
                        if abs(target.latitude - lat) < 1.0 and abs(target.longitude - lon) < 1.0:
                            bbox = target.bbox
                            if getattr(target, "zoom", None):
                                zoom = target.zoom
                            else:
                                from exploration.fallback_parser import FallbackParser
                                zoom = FallbackParser.calculate_zoom(bbox, default=11.5)

            # If bbox is missing, generate an appropriate bounding box around the target coordinates
            if not bbox and lat is not None and lon is not None:
                d_lat = 0.08
                d_lon = 0.08
                bbox = [lon - d_lon, lat - d_lat, lon + d_lon, lat + d_lat]

            aoi_geom = None
            if bbox:
                clean_bbox = GeoResolver._sanitize_bbox(bbox, lat, lon) or bbox
                bbox = clean_bbox
                min_lon, min_lat, max_lon, max_lat = bbox
                aoi_geom = {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [round(min_lon, 5), round(min_lat, 5)],
                            [round(max_lon, 5), round(min_lat, 5)],
                            [round(max_lon, 5), round(max_lat, 5)],
                            [round(min_lon, 5), round(max_lat, 5)],
                            [round(min_lon, 5), round(min_lat, 5)],
                        ]
                    ],
                }

            pitch_val = cmd.pitch if (cmd.pitch is not None and -90.0 <= cmd.pitch <= -20.0) else -50.0

            cam = {
                "latitude": lat,
                "longitude": lon,
                "zoom": zoom,
                "heading": cmd.heading or 0.0,
                "pitch": pitch_val,
                "duration": cmd.duration or 1.5,
            }
            details: Dict[str, Any] = {
                "camera": cam,
                "target_name": name,
            }
            if aoi_geom:
                details["aoi"] = aoi_geom
                details["bbox"] = bbox
            elif bbox:
                details["bbox"] = bbox

            msg = f"Centered map on {name} and delineated target region." if aoi_geom else f"Centered map on {name}."
            return CommandExecutionStatus.EXECUTED, msg, details, None

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
            cam = {"latitude": 20.5937, "longitude": 78.9629, "zoom": 4.5, "heading": 0.0, "pitch": -90.0}
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
                clean_bbox = GeoResolver._sanitize_bbox(
                    cmd.bbox,
                    (cmd.bbox[1] + cmd.bbox[3]) / 2,
                    (cmd.bbox[0] + cmd.bbox[2]) / 2,
                ) or cmd.bbox
                min_lon, min_lat, max_lon, max_lat = clean_bbox
                geom = {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [round(min_lon, 5), round(min_lat, 5)],
                            [round(max_lon, 5), round(min_lat, 5)],
                            [round(max_lon, 5), round(max_lat, 5)],
                            [round(min_lon, 5), round(max_lat, 5)],
                            [round(min_lon, 5), round(min_lat, 5)],
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
