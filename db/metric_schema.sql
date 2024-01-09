CREATE TABLE IF NOT EXISTS metric (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    explanation TEXT,
    FOREIGN KEY (log_id) REFERENCES chat(id)
);