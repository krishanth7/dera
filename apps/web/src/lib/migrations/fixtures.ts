import {
  ComparisonReportDto,
  MigrationPlanReportDto,
  MigrationReviewRequestDto,
  MigrationRiskReportDto,
  SqlMigrationArtifactDto,
} from './types';

export const SAMPLE_COMPARISON_REPORT: ComparisonReportDto = {
  report_id: 'rpt_cmp_5a821e',
  baseline_snapshot_id: 'snap_v1_orders_prod',
  target_snapshot_id: 'snap_v2_orders_staging',
  engine: 'postgresql',
  target_engine: 'postgresql',
  status: 'DIFFERENCES_FOUND',
  summary: {
    total_changes: 4,
    total_added: 2,
    total_removed: 1,
    total_modified: 1,
  },
  changes: [
    {
      change_id: 'chg_1',
      change_type: 'ADDED',
      object_type: 'TABLE',
      canonical_id: 'tbl_payment_methods',
      namespace: 'public',
      name: 'payment_methods',
      fingerprint: 'fp_chg_1',
    },
    {
      change_id: 'chg_2',
      change_type: 'ADDED',
      object_type: 'COLUMN',
      canonical_id: 'col_stripe_customer_id',
      namespace: 'public',
      name: 'stripe_customer_id',
      parent_name: 'payment_methods',
      fingerprint: 'fp_chg_2',
      property_differences: [
        { property_name: 'type', before_value: null, after_value: 'VARCHAR(255)' },
        { property_name: 'is_nullable', before_value: null, after_value: false },
      ],
    },
    {
      change_id: 'chg_3',
      change_type: 'MODIFIED',
      object_type: 'COLUMN',
      canonical_id: 'col_account_balance',
      namespace: 'public',
      name: 'balance_cents',
      parent_name: 'users',
      fingerprint: 'fp_chg_3',
      property_differences: [
        { property_name: 'type', before_value: 'INTEGER', after_value: 'BIGINT' },
      ],
    },
    {
      change_id: 'chg_4',
      change_type: 'REMOVED',
      object_type: 'TABLE',
      canonical_id: 'tbl_legacy_audit_cache',
      namespace: 'public',
      name: 'legacy_audit_cache',
      fingerprint: 'fp_chg_4',
    },
  ],
  report_fingerprint: '9f83a21b8c7456d9e012fa3829dc74826194acfe738291038472910283748291',
};

export const SAMPLE_RISK_REPORT: MigrationRiskReportDto = {
  report_id: 'mrk_4829bc',
  summary: {
    total_changes: 4,
    additive_changes: 2,
    removals: 1,
    modifications: 1,
    potentially_breaking: 1,
    requires_review: 2,
    total_risks: 2,
  },
  risk_assessments: [
    {
      risk_id: 'rsk_1',
      source_change_fingerprint: 'fp_chg_4',
      rule_id: 'RULE-DESTRUCTIVE-DROP',
      dimension: 'DATA_PRESERVATION',
      severity: 'HIGH',
      priority: 'P2_HIGH',
      reversibility: 'REQUIRES_PRESERVED_DATA',
      title: 'Dropped Table Data Loss',
      description: 'Dropping legacy_audit_cache will permanently erase table rows and indexes.',
      fingerprint: 'rsk_fp_1',
    },
    {
      risk_id: 'rsk_2',
      source_change_fingerprint: 'fp_chg_2',
      rule_id: 'RULE-ADD-NOT-NULL',
      dimension: 'SCHEMA_COMPATIBILITY',
      severity: 'MEDIUM',
      priority: 'P3_MEDIUM',
      reversibility: 'POTENTIALLY_REVERSIBLE',
      title: 'Non-Null Column Without Default',
      description: 'Adding stripe_customer_id as NOT NULL requires table backfill verification.',
      fingerprint: 'rsk_fp_2',
    },
  ],
  report_fingerprint: '57b29a8f4c10e395729108394857102938475620192837465019283746501928',
};

export const SAMPLE_PLAN_REPORT: MigrationPlanReportDto = {
  plan_id: 'plan_7c819a',
  plan_status: 'REQUIRES_MANUAL_DECISION',
  target_engine: 'postgresql',
  plan_fingerprint: '38a9bc71e0481928374650192837465019283746501928374650192837465019',
  summary: {
    total_operations: 4,
    supported_operations: 4,
    conditional_operations: 0,
    blocked_operations: 0,
    unsupported_operations: 0,
    manual_decision_gates_count: 2,
    dependency_edges_count: 2,
    stages_count: 2,
    destructive_operations_count: 1,
  },
  stages: [
    {
      stage_id: 'stage_1',
      stage_type: 'SCHEMA_MODIFICATION',
      stage_order: 1,
      operation_ids: ['op_create_tbl_payment_methods', 'op_add_col_stripe_customer_id', 'op_alter_col_balance'],
      description: 'Create base tables and column structures in dependency order.',
    },
    {
      stage_id: 'stage_2',
      stage_type: 'SCHEMA_MODIFICATION',
      stage_order: 2,
      operation_ids: ['op_drop_tbl_legacy_audit_cache'],
      description: 'Destructive table removal stage (requires data preservation sign-off).',
    },
  ],
  operations: [
    {
      operation_id: 'op_create_tbl_payment_methods',
      operation_type: 'CREATE_TABLE',
      target_object_id: 'tbl_payment_methods',
      target_object_name: 'payment_methods',
      namespace: 'public',
      table_name: 'payment_methods',
      prerequisite_operation_ids: [],
      dependent_operation_ids: ['op_add_col_stripe_customer_id'],
      engine_capability: 'SUPPORTED',
      review_priority: 'P4_LOW',
      is_destructive: false,
      is_blocked: false,
      blocking_reasons: [],
    },
    {
      operation_id: 'op_add_col_stripe_customer_id',
      operation_type: 'ADD_COLUMN',
      target_object_id: 'col_stripe_customer_id',
      target_object_name: 'stripe_customer_id',
      namespace: 'public',
      table_name: 'payment_methods',
      prerequisite_operation_ids: ['op_create_tbl_payment_methods'],
      dependent_operation_ids: [],
      engine_capability: 'SUPPORTED',
      review_priority: 'P3_MEDIUM',
      is_destructive: false,
      is_blocked: false,
      blocking_reasons: [],
    },
    {
      operation_id: 'op_alter_col_balance',
      operation_type: 'ALTER_COLUMN_TYPE',
      target_object_id: 'col_account_balance',
      target_object_name: 'balance_cents',
      namespace: 'public',
      table_name: 'users',
      prerequisite_operation_ids: [],
      dependent_operation_ids: [],
      engine_capability: 'SUPPORTED',
      review_priority: 'P4_LOW',
      is_destructive: false,
      is_blocked: false,
      blocking_reasons: [],
    },
    {
      operation_id: 'op_drop_tbl_legacy_audit_cache',
      operation_type: 'DROP_TABLE',
      target_object_id: 'tbl_legacy_audit_cache',
      target_object_name: 'legacy_audit_cache',
      namespace: 'public',
      table_name: 'legacy_audit_cache',
      prerequisite_operation_ids: [],
      dependent_operation_ids: [],
      engine_capability: 'SUPPORTED',
      review_priority: 'P2_HIGH',
      is_destructive: true,
      is_blocked: false,
      blocking_reasons: [],
    },
  ],
};

export const SAMPLE_SQL_ARTIFACT: SqlMigrationArtifactDto = {
  artifact_id: 'art_sql_847192',
  source_plan_id: 'plan_7c819a',
  dialect: 'POSTGRESQL',
  target_engine: 'postgresql',
  status: 'GENERATED_WITH_REVIEW_REQUIRED',
  artifact_fingerprint: '7391028475619283746501928374650192837465019283746501928374650192',
  rendered_sql_script: `-- ============================================================================
-- DERA MIGRATION SQL ARTIFACT
-- Dialect: POSTGRESQL
-- Source Plan: plan_7c819a
-- Baseline: snap_v1_orders_prod -> Target: snap_v2_orders_staging
-- STATUS: GENERATED FOR REVIEW — NOT EXECUTED
-- ============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS "public"."payment_methods" ();

ALTER TABLE "public"."payment_methods" ADD COLUMN "stripe_customer_id" VARCHAR(255) NOT NULL;

ALTER TABLE "public"."users" ALTER COLUMN "balance_cents" TYPE BIGINT;

DROP TABLE IF EXISTS "public"."legacy_audit_cache";

COMMIT;
`,
  summary: {
    total_statements: 4,
    destructive_statements: 1,
    review_required_statements: 1,
    transaction_blocks_count: 1,
    validation_issues_count: 0,
  },
  statements: [
    {
      statement_id: 'stmt_1',
      source_operation_id: 'op_create_tbl_payment_methods',
      source_operation_type: 'CREATE_TABLE',
      target_object_name: 'payment_methods',
      sql: 'CREATE TABLE IF NOT EXISTS "public"."payment_methods" ();',
      dialect: 'POSTGRESQL',
      execution_mode: 'TRANSACTIONAL',
      is_destructive: false,
      requires_manual_review: false,
    },
    {
      statement_id: 'stmt_2',
      source_operation_id: 'op_add_col_stripe_customer_id',
      source_operation_type: 'ADD_COLUMN',
      target_object_name: 'stripe_customer_id',
      sql: 'ALTER TABLE "public"."payment_methods" ADD COLUMN "stripe_customer_id" VARCHAR(255) NOT NULL;',
      dialect: 'POSTGRESQL',
      execution_mode: 'TRANSACTIONAL',
      is_destructive: false,
      requires_manual_review: true,
    },
    {
      statement_id: 'stmt_3',
      source_operation_id: 'op_alter_col_balance',
      source_operation_type: 'ALTER_COLUMN_TYPE',
      target_object_name: 'balance_cents',
      sql: 'ALTER TABLE "public"."users" ALTER COLUMN "balance_cents" TYPE BIGINT;',
      dialect: 'POSTGRESQL',
      execution_mode: 'TRANSACTIONAL',
      is_destructive: false,
      requires_manual_review: false,
    },
    {
      statement_id: 'stmt_4',
      source_operation_id: 'op_drop_tbl_legacy_audit_cache',
      source_operation_type: 'DROP_TABLE',
      target_object_name: 'legacy_audit_cache',
      sql: 'DROP TABLE IF EXISTS "public"."legacy_audit_cache";',
      dialect: 'POSTGRESQL',
      execution_mode: 'TRANSACTIONAL',
      is_destructive: true,
      requires_manual_review: true,
    },
  ],
  execution_notice: 'GENERATED FOR REVIEW — NOT EXECUTED',
};

export const SAMPLE_REVIEW_REQUEST: MigrationReviewRequestDto = {
  review_id: 'rev_gov_948210',
  workspace_id: 'ws_prod_01',
  artifact_id: 'art_sql_847192',
  artifact_fingerprint: '7391028475619283746501928374650192837465019283746501928374650192',
  status: 'UNDER_REVIEW',
  requester_id: 'eng_alice_lead',
  created_at: '2026-11-01T14:30:00Z',
  is_invalidated: false,
  export_eligibility: 'REVIEW_REQUIRED',
  safety_gate_results: [
    {
      gate_id: 'GATE-STATUS-001',
      status: 'PASS',
      rationale: 'SQL artifact status permitted for governance review.',
    },
    {
      gate_id: 'GATE-VALIDATION-002',
      status: 'PASS',
      rationale: 'Zero SQL structural validation issues detected.',
    },
    {
      gate_id: 'GATE-DESTRUCTIVE-003',
      status: 'REVIEW_REQUIRED',
      rationale: 'Artifact contains 1 destructive statement (DROP TABLE). Admin approval required.',
    },
  ],
  decisions: [
    {
      decision_id: 'dec_1',
      reviewer_id: 'eng_bob_staff',
      reviewer_role: 'editor',
      decision_type: 'APPROVE',
      reason: 'Schema structures verified. Clean type conversion.',
      timestamp: '2026-11-01T15:00:00Z',
    },
  ],
  audit_events: [
    {
      event_id: 'evt_1',
      actor_id: 'eng_alice_lead',
      event_type: 'REVIEW_CREATED',
      new_state: 'DRAFT',
      timestamp: '2026-11-01T14:30:00Z',
      event_hash: '9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b',
    },
    {
      event_id: 'evt_2',
      actor_id: 'eng_alice_lead',
      event_type: 'REVIEW_SUBMITTED',
      previous_state: 'DRAFT',
      new_state: 'SUBMITTED',
      timestamp: '2026-11-01T14:35:00Z',
      event_hash: '8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b9a8b7c6d5e4f3a2b1c0d9e',
    },
    {
      event_id: 'evt_3',
      actor_id: 'eng_bob_staff',
      event_type: 'DECISION_RECORDED',
      previous_state: 'SUBMITTED',
      new_state: 'UNDER_REVIEW',
      timestamp: '2026-11-01T15:00:00Z',
      event_hash: '7e6f5a4b3c2d1e0f9a8b9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d',
    },
  ],
};

export const SAMPLE_SNAPSHOTS: import('./types').SchemaSnapshotSummary[] = [
  {
    id: 'snap_v1_orders_prod',
    name: 'Orders DB - v1.0 Production Baseline',
    engine: 'postgresql',
    engine_version: '15.4',
    fingerprint: '9f83a21b8c7456d9e012fa3829dc74826194acfe738291038472910283748291',
    table_count: 24,
    view_count: 6,
    captured_at: '2026-11-01T12:00:00Z',
  },
  {
    id: 'snap_v2_orders_staging',
    name: 'Orders DB - v2.0 Staging Target',
    engine: 'postgresql',
    engine_version: '15.4',
    fingerprint: '8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b9a8b7c6d5e4f3a2b1c0d9e',
    table_count: 25,
    view_count: 6,
    captured_at: '2026-11-01T14:15:00Z',
  },
  {
    id: 'snap_v1_analytics_sqlite',
    name: 'Local Analytics DB (SQLite)',
    engine: 'sqlite',
    engine_version: '3.42.0',
    fingerprint: '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b',
    table_count: 8,
    view_count: 1,
    captured_at: '2026-11-01T10:00:00Z',
  },
];

export const SAMPLE_COMPARISON = SAMPLE_COMPARISON_REPORT;
export const SAMPLE_MIGRATION_PLAN = SAMPLE_PLAN_REPORT;
export const SAMPLE_GOVERNANCE_REVIEW = SAMPLE_REVIEW_REQUEST;
export const SAMPLE_AUDIT_EVENTS = SAMPLE_REVIEW_REQUEST.audit_events;
