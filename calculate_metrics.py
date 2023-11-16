import os
import sqlite3
import sys

import langcheck.metrics
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_type = 'azure'
openai.api_base = os.environ['AZURE_OPENAI_API_BASE']
openai.api_version = os.environ['AZURE_OPENAI_API_VERSION']
openai.api_key = os.environ['AZURE_OPENAI_API_KEY']

DATABASE = 'db/langcheckchat.db'


def add_metric_to_db(cursor,
                     metric_fn,
                     metric_args,
                     name,
                     log_id,
                     openai_args=None):
    metric_value = metric_fn(*metric_args)
    cursor.execute(f"UPDATE chat_log SET {name} = ? WHERE id = ?",
                   (metric_value.metric_values[0], log_id))
    if openai_args:
        metric_value_openai = metric_fn(*metric_args,
                                        model_type='openai',
                                        openai_args=openai_args)
        cursor.execute(f"UPDATE chat_log SET {name}_openai = ? WHERE id = ?",
                       (metric_value_openai.metric_values[0], log_id))


def main(log_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        request, response, source, language = cursor.execute(
            'SELECT request, response, source, language FROM chat_log WHERE id = ?',
            (log_id, )).fetchone()

    openai_args = {'engine': os.environ['AZURE_OPENAI_API_DEPLOYMENT']}
    with sqlite3.connect(DATABASE, isolation_level=None) as conn:
        cursor = conn.cursor()
        if language == 'en':
            # TODO: Factual consistency is a special case since the local
            # version of the metric is computed separately. Consider
            # refactoring this.
            factual_consistency_openai = langcheck.metrics.factual_consistency(
                response, source, model_type='openai', openai_args=openai_args)
            cursor.execute(
                "UPDATE chat_log SET factual_consistency_openai = ? WHERE id = ?",
                (factual_consistency_openai.metric_values[0], log_id))
            add_metric_to_db(cursor,
                             langcheck.metrics.toxicity, [request],
                             'request_toxicity',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(cursor,
                             langcheck.metrics.sentiment, [request],
                             'request_sentiment',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(cursor,
                             langcheck.metrics.fluency, [request],
                             'request_fluency',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(cursor, langcheck.metrics.flesch_reading_ease,
                             [request], 'request_readability', log_id)

            add_metric_to_db(cursor,
                             langcheck.metrics.toxicity, [response],
                             'response_toxicity',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(cursor,
                             langcheck.metrics.sentiment, [response],
                             'response_sentiment',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(cursor,
                             langcheck.metrics.fluency, [response],
                             'response_fluency',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(cursor, langcheck.metrics.flesch_reading_ease,
                             [response], 'response_readability', log_id)
            add_metric_to_db(cursor,
                             langcheck.metrics.ai_disclaimer_similarity,
                             [response], 'ai_disclaimer_similarity', log_id)
        else:
            # TODO: Factual consistency is a special case since the local
            # version of the metric is computed separately. Consider
            # refactoring this.
            factual_consistency_openai = langcheck.metrics.ja.factual_consistency(
                response, source, model_type='openai', openai_args=openai_args)
            cursor.execute(
                "UPDATE chat_log SET factual_consistency_openai = ? WHERE id = ?",
                (factual_consistency_openai.metric_values[0], log_id))
            add_metric_to_db(cursor,
                             langcheck.metrics.ja.toxicity, [request],
                             'request_toxicity',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(cursor,
                             langcheck.metrics.ja.sentiment, [request],
                             'request_sentiment',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(cursor,
                             langcheck.metrics.ja.fluency, [request],
                             'request_fluency',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(
                cursor, langcheck.metrics.ja.tateishi_ono_yamada_reading_ease,
                [request], 'request_readability', log_id)

            add_metric_to_db(cursor,
                             langcheck.metrics.ja.toxicity, [response],
                             'response_toxicity',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(cursor,
                             langcheck.metrics.ja.sentiment, [response],
                             'response_sentiment',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(cursor,
                             langcheck.metrics.ja.fluency, [response],
                             'response_fluency',
                             log_id,
                             openai_args=openai_args)
            add_metric_to_db(
                cursor, langcheck.metrics.ja.tateishi_ono_yamada_reading_ease,
                [response], 'response_readability', log_id)
            # TODO: Use japanese metrics once implemented
            add_metric_to_db(cursor,
                             langcheck.metrics.ai_disclaimer_similarity,
                             [response], 'ai_disclaimer_similarity', log_id)

        cursor.execute("UPDATE chat_log SET completed = 1 WHERE id = ?",
                       (log_id, ))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        log_id = sys.argv[1]
        main(int(log_id))