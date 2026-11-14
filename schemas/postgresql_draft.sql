-- EQAT Knowledge Base schema draft v0.2
-- PostgreSQL 16+. NOT APPLIED TO ANY LIVE DATABASE.
-- Versioned clinical artifacts must be immutable after approval.
CREATE TABLE source_document (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  url TEXT,
  edition TEXT,
  publisher TEXT,
  license_scope TEXT NOT NULL DEFAULT 'to_review',
  review_status TEXT NOT NULL DEFAULT 'unverified',
  UNIQUE (title, edition)
);
CREATE TABLE test_definition (
  code TEXT PRIMARY KEY,
  section TEXT NOT NULL,
  name TEXT NOT NULL,
  clinical_goal TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE test_revision (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  test_code TEXT NOT NULL REFERENCES test_definition(code),
  version TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('draft','review','approved','retired')),
  frequency_rule JSONB,
  method_category TEXT,
  applicability_rule JSONB,
  published_at TIMESTAMPTZ,
  UNIQUE(test_code,version)
);
CREATE TABLE sop_version (
  id TEXT PRIMARY KEY,
  test_code TEXT NOT NULL REFERENCES test_definition(code),
  version TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('draft','review','approved','retired')),
  sections JSONB NOT NULL,
  author_user_id TEXT,
  reviewer_user_id TEXT,
  approved_at TIMESTAMPTZ,
  UNIQUE(test_code, version)
);
CREATE TABLE criterion_version (
  id BIGINT GENERATED ALWAYS AS ID PRIMARY KEY,
  test_code TEXT NOT NULL REFERENCES test_definition(code),
  version TEXT NOT NULL,
  measurand TEXT NOT NULL,
  unit TEXT,
  expression JSONB NOT NULL,
  acceptance_basis TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('draft','review','approved','retired')),
  UNIQUE(test_code,version,measurand)
);
CREATE TABLE evidence_link (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  test_code TEXT REFERENCES test_definition(code),
  sop_id TEXT REFERENCES sop_version(id),
  source_id TEXT NOT NULL REFERENCES source_document(id),
  section_path TEXT,
  page_label TEXT,
  evidence_role TEXT NOT NULL DEFAULT 'method',
  verification_state TEXT NOT NULL DEFAULT 'reference_only',
  reviewed_by TEXT,
  reviewed_at TIMESTAMPTZ
);
CREATE TABLE machine (
  id TEXT PRIMARY KEY,
  vendor TEXT NOT NULL,
  model TEXT NOT NULL,
  machine_serial TEXT UNIQUE,
  active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE machine_feature (
  machine_id TEXT NOT NULL REFERENCES machine(id),
  feature_code TEXT NOT NULL,
  feature_state TEXT NOT NULL CHECK(feature_state IN ('present','absent','unknown')),
  software_version TEXT,
  effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
  effective_to DATE,
  PRIMARY KEY(machine_id,feature_code,effective_from)
);
CREATE TABLE qa_program_version (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  machine_id TEXT NOT NULL REFERENCES machine(id),
  version TEXT NOT NULL,
  state TEXT NOT NULL CHECK(state IN ('draft','review','approved','retired')),
  reason TEXT,
  generated_from JSONB,
  approved_by TEXT,
  approved_at TIMESTAMPTZ,
  UNIQUE(machine_id,version)
);
CREATE TABLE qa_program_item (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  program_id BIGINT NOT NULL REFERENCES qa_program_version(id),
  test_rev_id BIGINT NOT NULL REFERENCES test_revision(id),
  sop_id TEXT REFERENCES sop_version(id),
  criterion_id BIGINT REFERENCES criterion_version(id),
  applicability TEXT NOT NULL CHECK(applicability IN
    ('eligible_draft','pending_feature_confirmation','not_applicable','active')),
  reason TEXT,
  UNIQUE(program_id,test_rev_id)
);
CREATE TABLE measuring_device (
  id TEXT PRIMARY KEY,
  model TEXT NOT NULL,
  serial TEXT,
  calibration_due DATE,
  availability TEXT NOT NULL DEFAULT 'unverified'
);
CREATE TABLE qa_dataset (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  machine_id TEXT NOT NULL REFERENCES machine(id),
  source_type TEXT NOT NULL,
  imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  source_timestamp TIMESTAMPTZ,
  sha256 CHAR(64) NOT NULL,
  coordinate_frame TEXT,
  pseudonymized BOOLEAN NOT NULL DEFAULT FALSE,
  file_ref TEXT NOT NULL,
  UNIQUE(machine_id,sha256)
);
CREATE TABLE qa_execution (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  program_item_id BIGINT NOT NULL REFERENCES qa_program_item(id),
  performed_at TIMESTAMPTZ,
  status TEXT NOT NULL CHECK(status IN
    ('planned','performed','calculated','review_pending','approved','rejected','cancelled')),
  investigator TEXT,
  reviewer TEXT,
  analysis_version TEXT,
  measurement_device_id TEXT REFERENCES measuring_device(id),
  immutable_result JSONB,
  signed_at TIMESTAMPTZ
);
CREATE TABLE qa_execution_dataset (
  execution_id BIGINT NOT NULL REFERENCES qa_execution(id),
  dataset_id BIGINT NOT NULL REFERENCES qa_dataset(id),
  role TEXT NOT NULL DEFAULT 'input',
  PRIMARY KEY(execution_id,dataset_id,role)
);
CREATE TABLE service_event (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  machine_id TEXT NOT NULL REFERENCES machine(id),
  event_kind TEXT NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  details JSONB,
  post_service_qa_state TEXT NOT NULL DEFAULT 'pending'
);
CREATE TABLE audit_event (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  action TEXT NOT NULL,
  actor TEXT,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  before_data JSONB,
  after_data JSONB
);
-- Additional database policies/triggers required before clinical deployment:
-- enforce version immutability, RBAC, signatures, append-only audit log,
-- retention policy, backups, encryption, audit of access to files and PHI.
