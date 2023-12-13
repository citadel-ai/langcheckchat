import os
import sqlite3
import sys

import langcheck.metrics

from calculate_metrics import DATABASE, add_metric_to_db


def main(log_id, reference):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        request, response, language = cursor.execute(
            'SELECT request, response, language FROM chat_log WHERE id = ?',
            (log_id, )).fetchone()
    with sqlite3.connect(DATABASE, isolation_level=None) as conn:
        cursor = conn.cursor()
        if language == 'en':
            add_metric_to_db(cursor, langcheck.metrics.rouge1,
                            [response, reference, request], 'rouge1', log_id)
            add_metric_to_db(cursor, langcheck.metrics.rouge2,
                            [response, reference, request], 'rouge2', log_id)
            add_metric_to_db(cursor, langcheck.metrics.rougeL,
                            [response, reference, request], 'rougeL', log_id)
            add_metric_to_db(cursor, langcheck.metrics.semantic_similarity,
                            [response, reference, request], 'semantic_similarity', log_id)
        else:
            add_metric_to_db(cursor, langcheck.metrics.ja.rouge1,
                            [response, reference, request], 'rouge1', log_id)
            add_metric_to_db(cursor, langcheck.metrics.ja.rouge2,
                            [response, reference, request], 'rouge2', log_id)
            add_metric_to_db(cursor, langcheck.metrics.ja.rougeL,
                            [response, reference, request], 'rougeL', log_id)
            add_metric_to_db(cursor, langcheck.metrics.ja.semantic_similarity,
                            [response, reference, request], 'semantic_similarity', log_id)
        cursor.execute("UPDATE chat_log SET completed = 1 WHERE id = ?",
                       (log_id, ))


if __name__ == '__main__':
    if len(sys.argv) > 2:
        log_id = sys.argv[1]
        reference = sys.argv[2]
        main(int(log_id), reference)