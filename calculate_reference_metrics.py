import sys

import langcheck.metrics

import database as db
from calculate_metrics import Metric


def main(log_id, reference):
    chatlog = db.get_chatlog_by_id(log_id)
    request = chatlog['request']
    response = chatlog['response']
    language = chatlog['language']
    db.update_chatlog_by_id({'status': 'new', 'reference': reference}, log_id)

    metrics_to_compute = [
        Metric('rouge1', langcheck.metrics.rouge1, langcheck.metrics.ja.rouge1,
               [response, reference, request], True, False),
        Metric('rouge2', langcheck.metrics.rouge2, langcheck.metrics.ja.rouge2,
               [response, reference, request], True, False),
        Metric('rougeL', langcheck.metrics.rougeL, langcheck.metrics.ja.rougeL,
               [response, reference, request], True, False),
        Metric('semantic_similarity', langcheck.metrics.semantic_similarity,
               langcheck.metrics.ja.semantic_similarity,
               [response, reference, request], True, False)
    ]

    # First, add the metric names to the database, but don't yet compute the
    # metrics
    for metric in metrics_to_compute:
        metric.insert_metric_names_to_db(log_id)
    db.update_chatlog_by_id({'status': 'pending'}, log_id)

    # Then, compute the metrics and update the database
    for metric in metrics_to_compute:
        metric.compute_metrics_and_update_db(language)
    db.update_chatlog_by_id({'status': 'done'}, log_id)


if __name__ == '__main__':
    if len(sys.argv) > 2:
        log_id = sys.argv[1]
        reference = sys.argv[2]
        main(int(log_id), reference)
