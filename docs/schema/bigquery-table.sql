CREATE TABLE IF NOT EXISTS `methodic_demo.win_loss_responses` (
  participant_id STRING NOT NULL,
  study_id STRING NOT NULL,
  segment STRING,
  persona_summary STRING,
  conversation_status STRING NOT NULL,

  -- structured_fields (flat)
  primary_loss_reason STRING,
  secondary_loss_reason STRING,
  roi_clarity STRING,
  budget_timing STRING,
  procurement_friction STRING,
  security_concern STRING,
  competitor_pressure STRING,
  aha_moment_reached STRING,

  -- field_confidence (flat, FLOAT64, prefix conf_)
  conf_primary_loss_reason FLOAT64,
  conf_roi_clarity FLOAT64,
  conf_budget_timing FLOAT64,
  conf_procurement_friction FLOAT64,
  conf_security_concern FLOAT64,
  conf_competitor_pressure FLOAT64,
  conf_aha_moment_reached FLOAT64,

  -- coverage_state (flat, STRING, prefix cov_)
  cov_primary_loss_reason STRING,
  cov_roi_clarity STRING,
  cov_budget_timing STRING,
  cov_procurement_friction STRING,
  cov_security_concern STRING,
  cov_competitor_pressure STRING,
  cov_aha_moment_reached STRING,

  -- per-record quality
  quality_variable_coverage FLOAT64,
  quality_ambiguity_resolved BOOL,
  quality_evidence_linked BOOL,
  quality_requires_recontact BOOL,

  -- nested as JSON STRING
  evidence_json STRING,
  unresolved_ambiguities_json STRING,

  exported_at TIMESTAMP NOT NULL
);
