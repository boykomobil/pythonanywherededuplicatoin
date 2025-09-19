-- Add merge tracking fields to jobs table
ALTER TABLE jobs 
ADD COLUMN initial_found_record_ids TEXT NULL,
ADD COLUMN new_merged_record_id VARCHAR(255) NULL,
ADD COLUMN merge_count INT DEFAULT 0;

-- Add index for better query performance on unique_identifier
CREATE INDEX idx_unique_identifier ON jobs(unique_identifier);
