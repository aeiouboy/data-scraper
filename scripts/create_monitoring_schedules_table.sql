-- Create monitoring schedules table for Celery Beat configuration
-- This table stores schedule configurations that can be managed via UI

-- Drop existing table if needed
-- DROP TABLE IF EXISTS monitoring_schedules CASCADE;

-- Create monitoring schedules table
CREATE TABLE IF NOT EXISTS monitoring_schedules (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL,
    task_type VARCHAR(50) NOT NULL DEFAULT 'category_monitor', -- category_monitor, product_scrape, etc.
    description TEXT,
    
    -- Schedule configuration
    schedule_type VARCHAR(20) NOT NULL CHECK (schedule_type IN ('interval', 'cron')),
    schedule_value JSONB NOT NULL, -- For interval: {"hours": 6}, For cron: {"minute": "0", "hour": "*/6"}
    
    -- Task parameters
    task_params JSONB DEFAULT '{}', -- e.g., {"retailer_code": "HP", "force_full_scan": false}
    
    -- Status fields
    enabled BOOLEAN DEFAULT true,
    last_run TIMESTAMP WITH TIME ZONE,
    next_run TIMESTAMP WITH TIME ZONE,
    last_status VARCHAR(20) CHECK (last_status IN ('success', 'failure', 'running', NULL)),
    last_error TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    
    -- Constraints
    CONSTRAINT unique_task_name UNIQUE (task_name)
);

-- Create indexes
CREATE INDEX idx_monitoring_schedules_enabled ON monitoring_schedules(enabled);
CREATE INDEX idx_monitoring_schedules_task_type ON monitoring_schedules(task_type);
CREATE INDEX idx_monitoring_schedules_next_run ON monitoring_schedules(next_run);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_monitoring_schedules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_monitoring_schedules_updated_at
    BEFORE UPDATE ON monitoring_schedules
    FOR EACH ROW
    EXECUTE FUNCTION update_monitoring_schedules_updated_at();

-- Insert default schedules
INSERT INTO monitoring_schedules (task_name, task_type, description, schedule_type, schedule_value, task_params)
VALUES 
    -- Category monitoring for all retailers every 6 hours
    (
        'category_monitor_all',
        'category_monitor',
        'Monitor all retailer categories for changes',
        'interval',
        '{"hours": 6}',
        '{"force_full_scan": false}'
    ),
    -- HomePro specific monitoring every 4 hours
    (
        'category_monitor_hp',
        'category_monitor',
        'Monitor HomePro categories',
        'interval',
        '{"hours": 4}',
        '{"retailer_code": "HP", "force_full_scan": false}'
    ),
    -- Daily product price update at 2 AM
    (
        'daily_price_update',
        'product_scrape',
        'Update product prices daily',
        'cron',
        '{"minute": "0", "hour": "2"}',
        '{"update_type": "price_only"}'
    )
ON CONFLICT (task_name) DO NOTHING;

-- Create schedule history table for tracking runs
CREATE TABLE IF NOT EXISTS monitoring_schedule_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    schedule_id UUID NOT NULL REFERENCES monitoring_schedules(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failure', 'running')),
    result JSONB,
    error_message TEXT,
    
    -- Performance metrics
    duration_seconds INTEGER,
    items_processed INTEGER,
    items_failed INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for history
CREATE INDEX idx_schedule_history_schedule_id ON monitoring_schedule_history(schedule_id);
CREATE INDEX idx_schedule_history_started_at ON monitoring_schedule_history(started_at DESC);
CREATE INDEX idx_schedule_history_status ON monitoring_schedule_history(status);

-- Grant permissions (adjust based on your Supabase roles)
GRANT ALL ON monitoring_schedules TO authenticated;
GRANT ALL ON monitoring_schedule_history TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Add RLS policies if needed
ALTER TABLE monitoring_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitoring_schedule_history ENABLE ROW LEVEL SECURITY;

-- Policy to allow authenticated users to view schedules
CREATE POLICY "Allow authenticated users to view schedules"
    ON monitoring_schedules FOR SELECT
    TO authenticated
    USING (true);

-- Policy to allow authenticated users to update schedules
CREATE POLICY "Allow authenticated users to update schedules"
    ON monitoring_schedules FOR UPDATE
    TO authenticated
    USING (true);

-- Policy to allow authenticated users to view history
CREATE POLICY "Allow authenticated users to view history"
    ON monitoring_schedule_history FOR SELECT
    TO authenticated
    USING (true);

-- Policy to allow system to insert history
CREATE POLICY "Allow system to insert history"
    ON monitoring_schedule_history FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Add comments
COMMENT ON TABLE monitoring_schedules IS 'Stores schedule configurations for automated monitoring tasks';
COMMENT ON TABLE monitoring_schedule_history IS 'Tracks execution history of scheduled monitoring tasks';
COMMENT ON COLUMN monitoring_schedules.schedule_type IS 'Type of schedule: interval (e.g., every 6 hours) or cron (specific times)';
COMMENT ON COLUMN monitoring_schedules.schedule_value IS 'JSON configuration for the schedule. For interval: {"hours": 6}, For cron: {"minute": "0", "hour": "*/6"}';
COMMENT ON COLUMN monitoring_schedules.task_params IS 'JSON parameters passed to the task when executed';