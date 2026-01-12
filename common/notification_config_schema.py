"""
BigQuery table schema for notification configuration.

This table stores real email recipients for different alert severities.
No hardcoded emails - all recipients are stored in the database.
"""

CREATE_NOTIFICATION_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS `loan_data.notification_config` (
  config_id STRING NOT NULL,
  severity STRING NOT NULL,  -- CRITICAL, HIGH, MEDIUM, LOW
  role STRING NOT NULL,      -- risk_team, credit_head, cro, loan_officer, risk_committee
  email STRING NOT NULL,
  slack_channel STRING,
  active BOOL NOT NULL DEFAULT true,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP()
);
"""

# Sample data insertion for production use
# IMPORTANT: Replace these with REAL email addresses before deployment
INSERT_SAMPLE_RECIPIENTS = """
-- CRITICAL severity recipients
INSERT INTO `loan_data.notification_config` 
(config_id, severity, role, email, slack_channel, active, created_at, updated_at)
VALUES
  -- CRITICAL: All senior management
  (GENERATE_UUID(), 'CRITICAL', 'risk_team', 'risk.team@loanguard.ai', '#critical-alerts', true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
  (GENERATE_UUID(), 'CRITICAL', 'credit_head', 'credit.head@loanguard.ai', '#critical-alerts', true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
  (GENERATE_UUID(), 'CRITICAL', 'cro', 'cro@loanguard.ai', '#critical-alerts', true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
  
  -- HIGH: Risk team + responsible officer
  (GENERATE_UUID(), 'HIGH', 'risk_team', 'risk.team@loanguard.ai', '#loan-alerts', true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
  (GENERATE_UUID(), 'HIGH', 'loan_officer', 'loan.officer@loanguard.ai', '#loan-alerts', true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
  
  -- MEDIUM: Loan officer only
  (GENERATE_UUID(), 'MEDIUM', 'loan_officer', 'loan.officer@loanguard.ai', '#loan-monitoring', true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
  
  -- Portfolio summary recipients
  (GENERATE_UUID(), 'PORTFOLIO', 'cro', 'cro@loanguard.ai', NULL, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
  (GENERATE_UUID(), 'PORTFOLIO', 'credit_head', 'credit.head@loanguard.ai', NULL, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
  (GENERATE_UUID(), 'PORTFOLIO', 'risk_committee', 'risk.committee@loanguard.ai', NULL, true, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());
"""

# Query to verify recipients
VERIFY_RECIPIENTS_QUERY = """
SELECT 
  severity,
  role,
  email,
  active,
  created_at
FROM `loan_data.notification_config`
WHERE active = true
ORDER BY severity, role;
"""
