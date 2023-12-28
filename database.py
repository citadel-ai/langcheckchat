import sqlite3
from typing import Any, Dict, List, Optional

DATABASE_URL = 'db/langcheckchat.db'


def initialize_db():
    with open('db/chat_log_schema.sql', 'r') as file:
        sql_script = file.read()

    with sqlite3.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()
        cursor.executescript(sql_script)
        conn.commit()


def select_data(query: str,
                params: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    if params is None:
        params = {}

    with sqlite3.connect(DATABASE_URL) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        return cursor.execute(query, params).fetchall()


def edit_data(query: str, params: Optional[List[Any]] = None) -> Optional[int]:
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
    chat_logs = select_data(query, {'id': id})
    if len(chat_logs) == 1:
        return dict(chat_logs[0])
    return {}


def get_chatlogs(limit: int, offset: int) -> List[dict]:
    query = '''
        SELECT * FROM chat_log 
        ORDER BY timestamp 
        DESC LIMIT :limit OFFSET :offset
    '''
    chat_logs = select_data(query, {'limit': limit, 'offset': offset})
    return [dict(chat_log) for chat_log in chat_logs]


def insert_chatlog(data: Dict[str, Any]) -> Optional[int]:
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data.keys()])
    query = f'''
        INSERT INTO chat_log ({columns}) VALUES ({placeholders})
    '''
    return edit_data(query, list(data.values()))


def update_chatlog_by_id(data: Dict[str, Any], id) -> Optional[int]:
    set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
    query = f'''
        UPDATE chat_log SET {set_clause} WHERE id = {id}
    '''
    return edit_data(query, list(data.values()))
