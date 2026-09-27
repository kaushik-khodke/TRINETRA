-- Satellite Research Workspace MVP schema
-- PostgreSQL 16+ / PostGIS 3+
-- Apply through a migration tool in real environments.

BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS app;

CREATE TYPE app.organization_member_role AS ENUM ('owner', 'admin', 'researcher', 'viewer');
CREATE TYPE app.mission_status AS ENUM ('active', 'archived');
CREATE TYPE app.mission_member_role AS ENUM ('owner', 'editor', 'viewer');
CREATE TYPE app.aoi_source_type AS ENUM ('drawn', 'uploaded', 'derived');
CREATE TYPE app.asset_type AS ENUM ('uploaded', 'catalog_item', 'derived');
CREATE TYPE app.asset_status AS ENUM ('registered', 'validating', 'ready', 'warning', 'invalid', 'unavailable');
CREATE TYPE app.question_status AS ENUM ('draft', 'planned', 'executed', 'saved', 'archived');
CREATE TYPE app.plan_origin AS ENUM ('copilot', 'manual', 'template');
CREATE TYPE app.plan_status AS ENUM ('draft', 'validated', 'approved', 'superseded', 'rejected');
CREATE TYPE app.run_status AS ENUM (
  'queued', 'preparing', 'running', 'succeeded', 'succeeded_with_warnings',
  'failed', 'cancel_requested', 'cancelled'
);
CREATE TYPE app.output_type AS ENUM ('raster', 'vector', 'table', 'chart', 'thumbnail', 'report', 'log');
CREATE TYPE app.entry_type AS ENUM ('question', 'result', 'note', 'finding', 'decision');
CREATE TYPE app.annotation_type AS ENUM ('point', 'line', 'polygon', 'text');

CREATE OR REPLACE FUNCTION app.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TABLE app.users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  external_subject text NOT NULL UNIQUE,
  email text NOT NULL,
  display_name text NOT NULL,
  avatar_url text,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text NOT NULL UNIQUE,
  settings jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.organization_members (
  organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
  role app.organization_member_role NOT NULL DEFAULT 'researcher',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, user_id)
);

CREATE TABLE app.missions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE RESTRICT,
  name text NOT NULL,
  slug text NOT NULL,
  description text,
  status app.mission_status NOT NULL DEFAULT 'active',
  default_srid integer NOT NULL DEFAULT 4326,
  settings jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by uuid NOT NULL REFERENCES app.users(id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, slug)
);

CREATE TABLE app.mission_members (
  mission_id uuid NOT NULL REFERENCES app.missions(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
  role app.mission_member_role NOT NULL DEFAULT 'viewer',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (mission_id, user_id)
);

CREATE TABLE app.areas_of_interest (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id uuid NOT NULL REFERENCES app.missions(id) ON DELETE CASCADE,
  name text NOT NULL,
  geometry geometry(MultiPolygon, 4326) NOT NULL,
  bbox geometry(Polygon, 4326),
  start_at timestamptz,
  end_at timestamptz,
  source_type app.aoi_source_type NOT NULL DEFAULT 'drawn',
  source_asset_id uuid,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by uuid NOT NULL REFERENCES app.users(id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (ST_IsValid(geometry)),
  CHECK (end_at IS NULL OR start_at IS NULL OR end_at >= start_at)
);

CREATE TABLE app.catalog_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  external_id text NOT NULL,
  collection_id text NOT NULL,
  geometry geometry(MultiPolygon, 4326),
  bbox geometry(Polygon, 4326),
  acquired_at timestamptz,
  cloud_cover numeric CHECK (cloud_cover IS NULL OR (cloud_cover >= 0 AND cloud_cover <= 100)),
  orbit_direction text,
  polarizations text[] NOT NULL DEFAULT '{}',
  properties jsonb NOT NULL DEFAULT '{}'::jsonb,
  assets jsonb NOT NULL DEFAULT '{}'::jsonb,
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (provider, external_id)
);

CREATE TABLE app.assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id uuid NOT NULL REFERENCES app.missions(id) ON DELETE CASCADE,
  asset_type app.asset_type NOT NULL,
  title text NOT NULL,
  source_provider text,
  external_id text,
  collection_id text,
  catalog_item_id uuid REFERENCES app.catalog_items(id) ON DELETE RESTRICT,
  footprint geometry(MultiPolygon, 4326),
  acquired_at timestamptz,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  status app.asset_status NOT NULL DEFAULT 'registered',
  created_by uuid NOT NULL REFERENCES app.users(id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (mission_id, source_provider, external_id)
);

ALTER TABLE app.areas_of_interest
  ADD CONSTRAINT areas_of_interest_source_asset_fk
  FOREIGN KEY (source_asset_id) REFERENCES app.assets(id) ON DELETE SET NULL;

CREATE TABLE app.asset_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id uuid NOT NULL REFERENCES app.assets(id) ON DELETE CASCADE,
  version_number integer NOT NULL CHECK (version_number > 0),
  object_uri text,
  thumbnail_uri text,
  mime_type text,
  size_bytes bigint CHECK (size_bytes IS NULL OR size_bytes >= 0),
  sha256 text,
  crs_code text,
  width integer CHECK (width IS NULL OR width > 0),
  height integer CHECK (height IS NULL OR height > 0),
  band_count integer CHECK (band_count IS NULL OR band_count >= 0),
  resolution_x double precision CHECK (resolution_x IS NULL OR resolution_x > 0),
  resolution_y double precision CHECK (resolution_y IS NULL OR resolution_y > 0),
  nodata_value double precision,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  validation_report jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by uuid NOT NULL REFERENCES app.users(id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (asset_id, version_number),
  UNIQUE (sha256)
);

CREATE TABLE app.asset_bands (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_version_id uuid NOT NULL REFERENCES app.asset_versions(id) ON DELETE CASCADE,
  band_index integer NOT NULL CHECK (band_index > 0),
  name text NOT NULL,
  common_name text,
  wavelength_min_nm numeric,
  wavelength_max_nm numeric,
  scale_factor double precision,
  add_offset double precision,
  unit text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (asset_version_id, band_index),
  UNIQUE (asset_version_id, name)
);

CREATE TABLE app.questions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id uuid NOT NULL REFERENCES app.missions(id) ON DELETE CASCADE,
  created_by uuid NOT NULL REFERENCES app.users(id) ON DELETE RESTRICT,
  text text NOT NULL,
  context jsonb NOT NULL DEFAULT '{}'::jsonb,
  status app.question_status NOT NULL DEFAULT 'draft',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.analysis_plans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  question_id uuid NOT NULL REFERENCES app.questions(id) ON DELETE CASCADE,
  version_number integer NOT NULL CHECK (version_number > 0),
  created_by uuid NOT NULL REFERENCES app.users(id) ON DELETE RESTRICT,
  origin app.plan_origin NOT NULL,
  pipeline_key text NOT NULL,
  pipeline_version text NOT NULL,
  input_bindings jsonb NOT NULL DEFAULT '[]'::jsonb,
  aoi_id uuid REFERENCES app.areas_of_interest(id) ON DELETE RESTRICT,
  time_range jsonb NOT NULL DEFAULT '{}'::jsonb,
  parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
  assumptions jsonb NOT NULL DEFAULT '[]'::jsonb,
  validation_report jsonb NOT NULL DEFAULT '{}'::jsonb,
  expected_outputs jsonb NOT NULL DEFAULT '[]'::jsonb,
  estimated_compute jsonb NOT NULL DEFAULT '{}'::jsonb,
  status app.plan_status NOT NULL DEFAULT 'draft',
  approved_by uuid REFERENCES app.users(id) ON DELETE RESTRICT,
  approved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (question_id, version_number),
  CHECK ((status = 'approved') = (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);

CREATE TABLE app.analysis_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id uuid NOT NULL REFERENCES app.missions(id) ON DELETE CASCADE,
  question_id uuid NOT NULL REFERENCES app.questions(id) ON DELETE RESTRICT,
  analysis_plan_id uuid NOT NULL REFERENCES app.analysis_plans(id) ON DELETE RESTRICT,
  run_number integer NOT NULL CHECK (run_number > 0),
  status app.run_status NOT NULL DEFAULT 'queued',
  worker_job_id text,
  pipeline_key text NOT NULL,
  pipeline_version text NOT NULL,
  environment_digest text,
  started_at timestamptz,
  finished_at timestamptz,
  progress_percent numeric(5,2) NOT NULL DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
  error_code text,
  error_message text,
  resource_usage jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_by uuid NOT NULL REFERENCES app.users(id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (mission_id, run_number),
  CHECK (finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE app.run_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL REFERENCES app.analysis_runs(id) ON DELETE CASCADE,
  event_type text NOT NULL,
  stage text,
  message text,
  progress_percent numeric(5,2) CHECK (progress_percent IS NULL OR (progress_percent >= 0 AND progress_percent <= 100)),
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.run_outputs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL REFERENCES app.analysis_runs(id) ON DELETE CASCADE,
  output_type app.output_type NOT NULL,
  name text NOT NULL,
  object_uri text NOT NULL,
  tile_uri text,
  mime_type text,
  geometry geometry(MultiPolygon, 4326),
  statistics jsonb NOT NULL DEFAULT '{}'::jsonb,
  quality_flags jsonb NOT NULL DEFAULT '[]'::jsonb,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (run_id, name)
);

CREATE TABLE app.provenance_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL UNIQUE REFERENCES app.analysis_runs(id) ON DELETE CASCADE,
  manifest_uri text NOT NULL,
  source_assets jsonb NOT NULL DEFAULT '[]'::jsonb,
  pipeline jsonb NOT NULL DEFAULT '{}'::jsonb,
  parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
  software jsonb NOT NULL DEFAULT '{}'::jsonb,
  environment jsonb NOT NULL DEFAULT '{}'::jsonb,
  external_sources jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.notebook_entries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id uuid NOT NULL REFERENCES app.missions(id) ON DELETE CASCADE,
  question_id uuid REFERENCES app.questions(id) ON DELETE SET NULL,
  run_id uuid REFERENCES app.analysis_runs(id) ON DELETE SET NULL,
  title text NOT NULL,
  body text NOT NULL DEFAULT '',
  entry_type app.entry_type NOT NULL,
  visibility text NOT NULL DEFAULT 'mission' CHECK (visibility IN ('mission', 'private')),
  created_by uuid NOT NULL REFERENCES app.users(id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.annotations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id uuid NOT NULL REFERENCES app.missions(id) ON DELETE CASCADE,
  run_id uuid REFERENCES app.analysis_runs(id) ON DELETE SET NULL,
  created_by uuid NOT NULL REFERENCES app.users(id) ON DELETE RESTRICT,
  annotation_type app.annotation_type NOT NULL,
  geometry geometry(Geometry, 4326),
  label text,
  content text NOT NULL DEFAULT '',
  confidence numeric(5,4) CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE RESTRICT,
  mission_id uuid REFERENCES app.missions(id) ON DELETE SET NULL,
  actor_user_id uuid REFERENCES app.users(id) ON DELETE SET NULL,
  action text NOT NULL,
  entity_type text NOT NULL,
  entity_id uuid,
  request_id text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_missions_organization ON app.missions(organization_id);
CREATE INDEX idx_mission_members_user ON app.mission_members(user_id);
CREATE INDEX idx_aoi_geometry ON app.areas_of_interest USING GIST(geometry);
CREATE INDEX idx_aoi_mission ON app.areas_of_interest(mission_id);
CREATE INDEX idx_catalog_geometry ON app.catalog_items USING GIST(geometry);
CREATE INDEX idx_catalog_datetime ON app.catalog_items(acquired_at);
CREATE INDEX idx_catalog_collection ON app.catalog_items(collection_id);
CREATE INDEX idx_assets_mission_status ON app.assets(mission_id, status);
CREATE INDEX idx_assets_footprint ON app.assets USING GIST(footprint);
CREATE INDEX idx_assets_acquired_at ON app.assets(acquired_at);
CREATE INDEX idx_asset_versions_asset ON app.asset_versions(asset_id, version_number DESC);
CREATE INDEX idx_questions_mission ON app.questions(mission_id, created_at DESC);
CREATE INDEX idx_plans_question ON app.analysis_plans(question_id, version_number DESC);
CREATE INDEX idx_runs_mission_status ON app.analysis_runs(mission_id, status);
CREATE INDEX idx_run_events_run_time ON app.run_events(run_id, occurred_at);
CREATE INDEX idx_outputs_run ON app.run_outputs(run_id);
CREATE INDEX idx_outputs_geometry ON app.run_outputs USING GIST(geometry);
CREATE INDEX idx_notebook_mission_created ON app.notebook_entries(mission_id, created_at DESC);
CREATE INDEX idx_annotations_mission ON app.annotations(mission_id, created_at DESC);
CREATE INDEX idx_annotations_geometry ON app.annotations USING GIST(geometry);
CREATE INDEX idx_audit_mission_created ON app.audit_events(mission_id, created_at DESC);

CREATE TRIGGER users_updated_at BEFORE UPDATE ON app.users
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER organizations_updated_at BEFORE UPDATE ON app.organizations
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER organization_members_updated_at BEFORE UPDATE ON app.organization_members
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER missions_updated_at BEFORE UPDATE ON app.missions
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER mission_members_updated_at BEFORE UPDATE ON app.mission_members
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER aois_updated_at BEFORE UPDATE ON app.areas_of_interest
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER catalog_items_updated_at BEFORE UPDATE ON app.catalog_items
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER assets_updated_at BEFORE UPDATE ON app.assets
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER questions_updated_at BEFORE UPDATE ON app.questions
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER plans_updated_at BEFORE UPDATE ON app.analysis_plans
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER runs_updated_at BEFORE UPDATE ON app.analysis_runs
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER notebook_entries_updated_at BEFORE UPDATE ON app.notebook_entries
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();
CREATE TRIGGER annotations_updated_at BEFORE UPDATE ON app.annotations
FOR EACH ROW EXECUTE FUNCTION app.set_updated_at();

COMMIT;
