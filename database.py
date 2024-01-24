import sqlite3
from typing import Any, Dict, List, Optional

DATABASE_URL = 'db/langcheckchat.db'


def initialize_db(database_url: str = DATABASE_URL):
    with open('db/chat_log_schema.sql', 'r') as file:
        chat_log_schema_script = file.read()
    with open('db/metric_schema.sql', 'r') as file:
        metric_schema_script = file.read()

    with sqlite3.connect(database_url) as conn:
        cursor = conn.cursor()
        cursor.executescript(chat_log_schema_script)
        cursor.executescript(metric_schema_script)
        conn.commit()


def _select_data(query: str,
                 params: Optional[Dict[str, Any]] = None,
                 database_url: str = DATABASE_URL) -> List[sqlite3.Row]:
    '''Runs a SQL SELECT query on the SQLite database.
    '''
    if params is None:
        params = {}

    with sqlite3.connect(database_url) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        return cursor.execute(query, params).fetchall()


def _edit_data(query: str,
               params: Optional[List[Any]] = None,
               database_url: str = DATABASE_URL) -> Optional[int]:
    '''Runs a SQL INSERT or UPDATE query on the SQLite database.
    For a INSERT query, it returns the last inserted row id (lastrowid).
    '''
    if params is None:
        params = []

    with sqlite3.connect(database_url) as conn:
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


def get_chatlogs_and_metrics(limit: int, offset: int) -> List[dict]:
    '''
    Returns a list of chat logs and metrics, each of which is a dictionary with
    the following structure:
    {
        "<chat_log_id>": {
            "id": <chat_log_id>,
            "request": "...",
            "response": "...",
            "reference": "...",
            "timestamp": "<timestamp>",
            "source": "..",
            "language": "<language>",
            "status": "done",
            "metrics": {
                "ai_disclaimer_similarity": {"metric_value": <metric_value>, "explanation": "..."},
                "factual_consistency_openai": {"metric_value": <metric_value>, "explanation": "..."},
                ...
            }
        }
    }
    '''
    query = '''
        SELECT chat_log.*, metric.metric_name, metric.metric_value, metric.explanation
        FROM (
            SELECT * FROM chat_log
            ORDER BY timestamp DESC
            LIMIT :limit OFFSET :offset
        ) AS chat_log
        LEFT JOIN metric ON chat_log.id = metric.log_id
    '''
    all_logs = _select_data(query, {'limit': limit, 'offset': offset})
    metric_columns = ['metric_name', 'metric_value', 'explanation']

    # Each row in all_logs corresponds to a single metric. We want to group
    # together all the metrics for a single chat log.
    id_to_logs = {}
    for log in all_logs:
        id = log['id']
        if id not in id_to_logs:
            chat_log = {
                k: log[k]
                for k in log.keys() if k not in metric_columns
            }
            id_to_logs[id] = chat_log
            id_to_logs[id]['metrics'] = {}
        id_to_logs[id]['metrics'][log['metric_name']] = {
            'metric_value': log['metric_value'],
            'explanation': log['explanation']
        }
    return list(id_to_logs.values())


def get_comparison_chatlogs_and_metrics(limit: int, offset: int) -> List[dict]:
    '''
    Returns a list of chat logs and metrics for Database A and Database B, each
    of which is a dictionary with the following structure:
    {
        "<chat_log_id_a>": {
            "request_a": "...",
            "response_a": "...",
            "response_b": "...",
            "reference_a": "...",
            "timestamp_a": "<timestamp>",
            "source_a": "..",
            "source_b": "..",
            "language_a": "<language>",
            "status_a": "done",
            "metrics_a": {
                "ai_disclaimer_similarity": {"metric_value": <metric_value>, "explanation": "..."},
                "factual_consistency_openai": {"metric_value": <metric_value>, "explanation": "..."},
                ...
            },
            "metrics_b": {
                "ai_disclaimer_similarity": {"metric_value": <metric_value>, "explanation": "..."},
                "factual_consistency_openai": {"metric_value": <metric_value>, "explanation": "..."},
                ...
            }
        }
    }
    '''
    query_a = '''
        SELECT chat_log.*, metric.metric_name, metric.metric_value, metric.explanation
        FROM (
            SELECT * FROM chat_log
            ORDER BY timestamp DESC
            LIMIT :limit OFFSET :offset
        ) AS chat_log
        LEFT JOIN metric ON chat_log.id = metric.log_id
    '''
    a_logs = _select_data(query_a,
                          params={
                              'limit': limit,
                              'offset': offset
                          },
                          database_url='db/evaluation_results_0121.db')
    query_b = '''
        SELECT chat_log.*, metric.metric_name, metric.metric_value, metric.explanation
        FROM (
            SELECT * FROM chat_log
            ORDER BY timestamp DESC
        ) AS chat_log
        LEFT JOIN metric ON chat_log.id = metric.log_id
    '''
    b_logs = _select_data(query_b,
                          database_url='db/evaluation_results_0123-gpt4.db')
    metric_columns = ['metric_name', 'metric_value', 'explanation']

    # Each row in a_logs corresponds to a single metric. We want to group
    # together all the metrics for a single chat log.
    id_to_logs = {}
    request_a_to_id = {}
    for log in a_logs:
        id = log['id']
        if id not in id_to_logs:
            # Append '_a' to the keys to distinguish them from the keys in
            # b_logs
            chat_log = {
                f'{k}_a': log[k]
                for k in log.keys() if k not in metric_columns
            }
            id_to_logs[id] = chat_log
            id_to_logs[id]['metrics_a'] = {}
            id_to_logs[id]['metrics_b'] = {}
            # Store the mapping from request to id
            request_a_to_id[log['request']] = id
        id_to_logs[id]['metrics_a'][log['metric_name']] = {
            'metric_value': log['metric_value'],
            'explanation': log['explanation']
        }

    for log in b_logs:
        request_b = log['request']
        # Ignore this log if the request does not match any of the requests in
        # a_logs
        if request_b not in request_a_to_id:
            continue
        a_id = request_a_to_id[request_b]

        # Add response_b and source_b to the logs. Note that these may already
        # have been added (since each row in b_logs corresponds to a single
        # metric), but they should be the same so it doesn't matter.
        id_to_logs[a_id]['response_b'] = log['response']
        id_to_logs[a_id]['source_b'] = log['source']

        # Add the metrics from b_logs to the logs
        id_to_logs[a_id]['metrics_b'][log['metric_name']] = {
            'metric_value': log['metric_value'],
            'explanation': log['explanation']
        }
    return list(id_to_logs.values())


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


def insert_metric(log_id: int, metric_name: str, metric_value: Optional[float],
                  explanation: Optional[str]) -> int:
    col_names = ['log_id', 'metric_name', 'metric_value', 'explanation']
    columns = ', '.join(col_names)
    placeholders = ', '.join(['?' for _ in col_names])
    query = f'''
        INSERT INTO metric ({columns}) VALUES ({placeholders})
    '''
    id = _edit_data(query, [log_id, metric_name, metric_value, explanation])
    assert id is not None
    return id


def update_metric_by_id(metric_value: float, explanation: Optional[str],
                        id: int) -> None:
    set_clause = ', '.join(['metric_value = ?', 'explanation = ?'])
    query = f'''
        UPDATE metric SET {set_clause} WHERE id = {id}
    '''
    _edit_data(query, [metric_value, explanation])
    return


def get_metrics_by_log_id(log_id: int) -> Dict[str, Dict[str, Any]]:
    query = '''
        SELECT * FROM metric
        WHERE log_id = :log_id
    '''
    metrics = _select_data(query, {'log_id': log_id})
    return {
        metric['metric_name']: {
            'metric_value': metric['metric_value'],
            'explanation': metric['explanation']
        }
        for metric in metrics
    }
