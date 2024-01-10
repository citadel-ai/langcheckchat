CREATE TABLE IF NOT EXISTS chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request TEXT NOT NULL,
    response TEXT NOT NULL,
    reference TEXT,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    language TEXT NOT NULL,
    status TEXT default 'new'  /* new, pending, done */
);
