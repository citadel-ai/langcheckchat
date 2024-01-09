import sqlite3
from typing import Any, Dict, List, Optional

DATABASE_URL = 'db/langcheckchat.db'


def initialize_db():
    with open('db/chat_log_schema.sql', 'r') as file:
        chat_log_schema_script = file.read()
    with open('db/metric_schema.sql', 'r') as file:
        metric_schema_script = file.read()

    with sqlite3.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()
        cursor.executescript(chat_log_schema_script)
        cursor.executescript(metric_schema_script)
        conn.commit()


def _select_data(query: str,
                 params: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    '''Runs a SQL SELECT query on the SQLite database.
    '''
    if params is None:
        params = {}

    with sqlite3.connect(DATABASE_URL) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        return cursor.execute(query, params).fetchall()


def _edit_data(query: str,
               params: Optional[List[Any]] = None) -> Optional[int]:
    '''Runs a SQL INSERT or UPDATE query on the SQLite database.
    For a INSERT query, it returns the last inserted row id (lastrowid).
    '''
    if params is None:
        params = []

    with sqlite3.connect(DATABASE_URL) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.lastrowid


def get_chatlog_by_id(id: int) -> Dict[str, Any]:
    query = '''
        SELECT * FROM chat_log
        WHERE id = :id
    '''
    chat_logs = _select_data(query, {'id': id})
    if len(chat_logs) == 1:
        return dict(chat_logs[0])
    return {}


def get_chatlogs(limit: int, offset: int) -> List[dict]:
    query = '''
        SELECT * FROM chat_log
        ORDER BY timestamp
        DESC LIMIT :limit OFFSET :offset
    '''
    chat_logs = _select_data(query, {'limit': limit, 'offset': offset})
    return [dict(chat_log) for chat_log in chat_logs]


def insert_chatlog(data: Dict[str, Any]) -> int:
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data.keys()])
    query = f'''
        INSERT INTO chat_log ({columns}) VALUES ({placeholders})
    '''
    id = _edit_data(query, list(data.values()))
    assert id is not None
    return id


def update_chatlog_by_id(data: Dict[str, Any], id) -> None:
    set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
    query = f'''
        UPDATE chat_log SET {set_clause} WHERE id = {id}
    '''
    _edit_data(query, list(data.values()))
    return


def insert_metric(log_id: int, metric_name: str, metric_value: float,
                  explanation: Optional[str]) -> None:
    col_names = ['log_id', 'metric_name', 'metric_value', 'explanation']
    columns = ', '.join(col_names)
    placeholders = ', '.join(['?' for _ in col_names])
    query = f'''
        INSERT INTO metric ({columns}) VALUES ({placeholders})
    '''
    _edit_data(query, [log_id, metric_name, metric_value, explanation])
    return
