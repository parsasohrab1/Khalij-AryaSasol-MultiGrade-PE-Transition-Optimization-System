CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE TABLE IF NOT EXISTS dcs_samples (
  ts TIMESTAMPTZ NOT NULL, unit TEXT NOT NULL, current_grade TEXT NOT NULL,
  hydrogen_ratio DOUBLE PRECISION, comonomer_ratio DOUBLE PRECISION,
  catalyst_activity_pct DOUBLE PRECISION, melt_flow_index DOUBLE PRECISION,
  density_g_cm3 DOUBLE PRECISION, is_transition SMALLINT, off_spec_flag SMALLINT,
  production_tph DOUBLE PRECISION);
SELECT create_hypertable('dcs_samples', 'ts', if_not_exists => TRUE);
CREATE TABLE IF NOT EXISTS transition_log (  -- FR-LOOP-01 closed-loop record
  ts TIMESTAMPTZ NOT NULL, unit TEXT NOT NULL, src TEXT NOT NULL, dst TEXT NOT NULL,
  actual_time_h DOUBLE PRECISION, actual_waste_t DOUBLE PRECISION,
  predicted_time_h DOUBLE PRECISION, predicted_waste_t DOUBLE PRECISION);
