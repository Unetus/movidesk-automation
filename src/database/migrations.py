"""Database schema migrations."""


def get_schema() -> str:
    """
    Get the complete database schema.
    
    Returns:
        SQL script to create all tables and indexes
    """
    return """
-- ============================================
-- REPORTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generated_at DATETIME NOT NULL,
    agent_email TEXT NOT NULL,
    total_new INTEGER DEFAULT 0,
    total_overdue INTEGER DEFAULT 0,
    total_expiring INTEGER DEFAULT 0,
    total_summarized INTEGER DEFAULT 0,
    email_sent BOOLEAN DEFAULT FALSE,
    email_subject TEXT,
    execution_time_seconds REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- REPORT TICKETS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS report_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    ticket_id INTEGER NOT NULL,
    ticket_number TEXT,
    subject TEXT,
    client_name TEXT,
    status TEXT,
    base_status TEXT,
    urgency TEXT,
    category TEXT,
    created_date DATETIME,
    last_update DATETIME,
    sla_solution_date DATETIME,
    is_overdue BOOLEAN DEFAULT FALSE,
    days_overdue INTEGER DEFAULT 0,
    section TEXT NOT NULL,  -- 'new', 'overdue', 'expiring'
    movidesk_url TEXT,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE,
    UNIQUE(report_id, ticket_id)
);

-- ============================================
-- AI SUMMARIES CACHE TABLE (KEY FEATURE!)
-- ============================================
CREATE TABLE IF NOT EXISTS ai_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL UNIQUE,
    ticket_number TEXT,
    subject TEXT,
    summary TEXT NOT NULL,
    model_used TEXT DEFAULT 'llama-3.3-70b-versatile',
    tokens_used INTEGER,
    generated_at DATETIME NOT NULL,
    last_used_at DATETIME,
    use_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_reports_generated_at 
    ON reports(generated_at);

CREATE INDEX IF NOT EXISTS idx_reports_agent_email 
    ON reports(agent_email);

CREATE INDEX IF NOT EXISTS idx_report_tickets_report_id 
    ON report_tickets(report_id);

CREATE INDEX IF NOT EXISTS idx_report_tickets_ticket_id 
    ON report_tickets(ticket_id);

CREATE INDEX IF NOT EXISTS idx_report_tickets_section 
    ON report_tickets(section);

CREATE INDEX IF NOT EXISTS idx_ai_summaries_ticket_id 
    ON ai_summaries(ticket_id);

CREATE INDEX IF NOT EXISTS idx_ai_summaries_generated_at 
    ON ai_summaries(generated_at);
"""
