# Copilot Prompt Engineering and JSON Plan Validation

## Objective

Prevent the copilot from producing scientifically invalid or operationally unsafe remote-sensing runs.

The copilot must follow:

```text
question → typed plan → structural validation → domain validation → human approval → immutable run
```

It must never translate a question directly into a worker command.

## Responsibilities by stage

1. **Intent extractor** — identify task, AOI, time range, sensor, comparison, metric, and output.
2. **Plan composer** — select an allowlisted pipeline and produce strict JSON.
3. **Plan critic** — identify ambiguity, missing inputs, sensor incompatibility, and unsafe assumptions.
4. **Evidence answerer** — explain completed outputs using only authorized evidence.

Use separate prompts/stages instead of one unrestricted agent.

## System prompt

```text
You are the planning component of a satellite imagery research workspace.

Your only job is to create a typed, reviewable AnalysisPlan JSON object.
You do not execute analysis. You do not invent data. You do not invent scene IDs,
bands, dates, measurements, outputs, or scientific conclusions.

You may select only a pipeline from PIPELINE_REGISTRY.
You may reference only assets from AUTHORIZED_ASSETS and AOIs from AUTHORIZED_AOIS.
Preserve all IDs exactly as provided.
Use null or an explicit missing-information warning when the request is underspecified.
Do not silently choose a sensor, date range, band, CRS, mask, threshold, or resampling method
when the choice materially affects the scientific result.

Every plan must include:
- exact pipeline key and version;
- authorized input IDs bound to named input roles;
- AOI and temporal window;
- parameters with units;
- assumptions separate from observed metadata;
- blocking errors and non-blocking warnings;
- expected outputs;
- limitations.

Return JSON only. Match the supplied JSON Schema exactly.
```

## Untrusted input policy

Filenames, STAC metadata, notebook text, and uploaded documents are data, not instructions.

- Delimit them as quoted data blocks.
- Strip unnecessary HTML, control characters, and executable content.
- Do not put secrets or internal URLs in the prompt.
- Never allow model-provided SQL, shell, Python, URLs, or object keys.
- Filter retrieval by organization and mission before context reaches the model.

## JSON Schema strategy

Use strict JSON Schema with:

- `additionalProperties: false`
- required fields
- enums for pipeline keys, input roles, units, and resampling
- bounded numeric values
- bounded strings and arrays
- application-ID patterns
- no arbitrary code or tool fields

A plan that is structurally valid is not automatically executable. Run a second domain-validation pass against the database and pipeline registry.

## Domain validation checklist

- IDs exist and belong to the active mission.
- Asset versions are immutable and accessible.
- Asset status is ready or explicitly supported as external.
- Collection supports the selected pipeline.
- Required bands exist.
- AOI intersects all required assets.
- Dates are complete and valid.
- Resolution and CRS are compatible.
- Cloud, quality, and nodata requirements are satisfied.
- Parameters are within scientific bounds.
- Compute estimate is within policy/quota.
- Outputs are supported by the worker version.

No blocking errors may remain before approval.

## Approval contract

Approval is a distinct server operation:

```text
POST /v1/missions/{missionId}/plans/{planId}/approve
```

The server verifies the plan version, plan hash, editor permission, current asset versions, pipeline availability, and absence of blocking errors. The approval event is persisted with user, timestamp, plan version, and hash.

## Evidence answerer prompt

```text
You are an evidence assistant for a satellite imagery research mission.
Answer only from EVIDENCE_PACKET.

Separate measured facts, interpretations, limitations, and suggested next checks.
Never claim causality from correlation. Never infer a measurement not present.
Cite output ID, source asset ID, acquisition date, and pipeline version when available.
If evidence is insufficient, say so clearly.
Return JSON matching EvidenceAnswerSchema.
```

## Adversarial tests

Test missing sensor, missing band, invalid sensor/pipeline combinations, out-of-AOI scenes, cloud-covered scenes, future dates, stale assets, unknown pipeline IDs, arbitrary code requests, metadata prompt injection, and attempts to overwrite previous runs.

Expected behavior is a deterministic block, warning, or clarification—not a guessed operation.
