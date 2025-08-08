-- Initialize PostgreSQL database for Survey Data Processing Application
-- This script sets up the database with proper permissions and initial configuration

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for performance
-- These will be created by Django migrations, but we can prepare the database

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE statathon_db TO statathon_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO statathon_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO statathon_user;

-- Set up initial configuration
ALTER DATABASE statathon_db SET timezone TO 'UTC';

-- Create a function for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Insert initial configuration data (will be handled by Django fixtures)
-- This is just to ensure the database is properly set up