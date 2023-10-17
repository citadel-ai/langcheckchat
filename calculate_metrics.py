import sqlite3
import sys
import langcheck.metrics

DATABASE = 'db/langcheckchat.db'


def main(log_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        request, response, _, language = cursor.execute(
            'SELECT request, response, source, language FROM chat_log WHERE id = ?',
            (log_id, )).fetchone()

    with sqlite3.connect(DATABASE, isolation_level=None) as conn:
        cursor = conn.cursor()
        if language == 'en':
            request_toxicity = langcheck.metrics.toxicity(
                request).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET request_toxicity = ? WHERE id = ?",
                (request_toxicity, log_id))
            request_fluency = langcheck.metrics.toxicity(
                request).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET request_fluency = ? WHERE id = ?",
                (request_fluency, log_id))
            request_sentiment = langcheck.metrics.sentiment(
                request).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET request_sentiment = ? WHERE id = ?",
                (request_sentiment, log_id))
            request_fluency = langcheck.metrics.fluency(
                request).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET request_fluency = ? WHERE id = ?",
                (request_fluency, log_id))
            request_readability = langcheck.metrics.flesch_reading_ease(
                request).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET request_readability = ? WHERE id = ?",
                (request_readability, log_id))

            response_toxicity = langcheck.metrics.toxicity(
                response).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET response_toxicity = ? WHERE id = ?",
                (response_toxicity, log_id))
            response_sentiment = langcheck.metrics.sentiment(
                response).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET response_sentiment = ? WHERE id = ?",
                (response_sentiment, log_id))
            response_fluency = langcheck.metrics.fluency(
                response).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET response_fluency = ? WHERE id = ?",
                (response_fluency, log_id))
            response_readability = langcheck.metrics.flesch_reading_ease(
                response).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET response_readability = ? WHERE id = ?",
                (response_readability, log_id))
            ai_disclaimer_similarity = langcheck.metrics.ai_disclaimer_similarity(
                response).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET ai_disclaimer_similarity = ? WHERE id = ?",
                (ai_disclaimer_similarity, log_id))
        else:
            request_toxicity = langcheck.metrics.ja.toxicity(
                request).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET request_toxicity = ? WHERE id = ?",
                (request_toxicity, log_id))
            request_fluency = langcheck.metrics.ja.fluency(
                request).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET request_fluency = ? WHERE id = ?",
                (request_fluency, log_id))
            request_sentiment = langcheck.metrics.ja.sentiment(
                request).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET request_sentiment = ? WHERE id = ?",
                (request_sentiment, log_id))
            request_fluency = langcheck.metrics.ja.fluency(
                request).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET request_fluency = ? WHERE id = ?",
                (request_fluency, log_id))
            request_readability = langcheck.metrics.ja.tateishi_ono_yamada_reading_ease(
                request).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET request_readability = ? WHERE id = ?",
                (request_readability, log_id))

            response_toxicity = langcheck.metrics.ja.toxicity(
                response).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET response_toxicity = ? WHERE id = ?",
                (response_toxicity, log_id))
            response_sentiment = langcheck.metrics.ja.sentiment(
                response).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET response_sentiment = ? WHERE id = ?",
                (response_sentiment, log_id))
            response_fluency = langcheck.metrics.ja.fluency(
                response).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET response_fluency = ? WHERE id = ?",
                (response_fluency, log_id))
            response_readability = langcheck.metrics.ja.tateishi_ono_yamada_reading_ease(
                response).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET response_readability = ? WHERE id = ?",
                (response_readability, log_id))

            # TODO: Use japanese metrics once implemented
            ai_disclaimer_similarity = langcheck.metrics.ai_disclaimer_similarity(
                response).metric_values[0]
            cursor.execute(
                "UPDATE chat_log SET ai_disclaimer_similarity = ? WHERE id = ?",
                (ai_disclaimer_similarity, log_id))

        cursor.execute("UPDATE chat_log SET completed = 1 WHERE id = ?",
                       (log_id, ))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        log_id = sys.argv[1]
        main(int(log_id))