CREATE TABLE IF NOT EXISTS jobs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  enqueued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  unique_identifier VARCHAR(255) NOT NULL,
  dry_run TINYINT(1) DEFAULT 0,
  attempts INT DEFAULT 0,
  status ENUM('queued','working','done','error') DEFAULT 'queued',
  last_error TEXT
);
