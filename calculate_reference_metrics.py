import sys

import langcheck.metrics

import database as db
from calculate_metrics import add_metric_to_db


def main(log_id, reference):
    chatlog = db.get_chatlog_by_id(log_id)
    request = chatlog['request']
    response = chatlog['response']
    language = chatlog['language']
    db.update_chatlog_by_id({'completed': 0, 'reference': reference}, log_id)
    if language == 'en':
        add_metric_to_db(langcheck.metrics.rouge1,
                         [response, reference, request], 'rouge1', log_id)
        add_metric_to_db(langcheck.metrics.rouge2,
                         [response, reference, request], 'rouge2', log_id)
        add_metric_to_db(langcheck.metrics.rougeL,
                         [response, reference, request], 'rougeL', log_id)
        add_metric_to_db(langcheck.metrics.semantic_similarity,
                         [response, reference, request],
                         'semantic_similarity', log_id)
    else:
        add_metric_to_db(langcheck.metrics.ja.rouge1,
                         [response, reference, request], 'rouge1', log_id)
        add_metric_to_db(langcheck.metrics.ja.rouge2,
                         [response, reference, request], 'rouge2', log_id)
        add_metric_to_db(langcheck.metrics.ja.rougeL,
                         [response, reference, request], 'rougeL', log_id)
        add_metric_to_db(langcheck.metrics.ja.semantic_similarity,
                         [response, reference, request],
                         'semantic_similarity', log_id)
    db.update_chatlog_by_id({'completed': 1}, log_id)


if __name__ == '__main__':
    if len(sys.argv) > 2:
        log_id = sys.argv[1]
        reference = sys.argv[2]
        main(int(log_id), reference)
