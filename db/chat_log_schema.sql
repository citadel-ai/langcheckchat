CREATE TABLE chat_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
