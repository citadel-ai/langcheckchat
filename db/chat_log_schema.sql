CREATE TABLE chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    language TEXT NOT NULL,
    request_toxicity REAL,
    request_sentiment REAL,
    request_fluency REAL,
    request_readability REAL,
    response_toxicity REAL,
    response_sentiment REAL,
    response_fluency REAL,
    response_readability REAL,
    ai_disclaimer_similarity REAL,
    factual_consistency REAL,
    completed BOOLEAN default 0
);
