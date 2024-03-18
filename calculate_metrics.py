import os
import sys
from typing import Optional, Tuple

import langcheck.metrics
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

import database as db

load_dotenv()


def add_init_to_db(request, response, source, language, score, explanation,
                   timestamp) -> int:
    if os.environ['ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True':
        log_id = db.insert_chatlog({
            'request': request,
            'response': response,
            'source': source,
            'language': language,
            'timestamp': timestamp
        })
        db.insert_metric(log_id, 'factual_consistency', score, None)
    else:
        log_id = db.insert_chatlog({
            'request': request,
            'response': response,
            'source': source,
            'language': language,
            'timestamp': timestamp
        })
        db.insert_metric(log_id, 'factual_consistency_openai', score,
                         explanation)
    # For type check
    assert log_id is not None
    return log_id


class Metric:

    def __init__(self, metric_name, metric_fns, args, compute_local,
                 compute_openai):
        self.metric_name = metric_name
        self.metric_fns = metric_fns
        self.args = args
        self.compute_local = compute_local
        self.compute_openai = compute_openai
        assert self.compute_local or self.compute_openai, \
            "At least one of compute_local and compute_openai must be True"
        self.local_metric_id = None
        self.openai_metric_id = None

    def insert_metric_names_to_db(self, log_id):
        if self.compute_local:
            self.local_metric_id = db.insert_metric(log_id, self.metric_name,
                                                    None, None)
        if self.compute_openai:
            self.openai_metric_id = db.insert_metric(
                log_id, f"{self.metric_name}_openai", None, None)

    def compute_local_metric(self, language):
        assert language in self.metric_fns
        metric_fn = self.metric_fns[language]
        metric_result = metric_fn(*self.args)
        return metric_result.metric_values[0]

    def compute_openai_metric(self, language):
        assert language in self.metric_fns
        metric_fn = self.metric_fns[language]
        assert os.environ['LANGCHECK_OPENAI_API_TYPE'] in ['openai', 'azure']
        if os.environ['LANGCHECK_OPENAI_API_TYPE'] == 'azure':
            model_type = 'azure_openai'
            openai_client = AzureOpenAI(
                api_key=os.environ['LANGCHECK_AZURE_OPENAI_KEY'],
                api_version=os.environ['LANGCHECK_OPENAI_API_VERSION'],
                azure_endpoint=os.environ['LANGCHECK_AZURE_OPENAI_ENDPOINT'])
            openai_args = {
                'model': os.environ['LANGCHECK_AZURE_OPENAI_API_DEPLOYMENT']
            }
        else:
            model_type = 'openai'
            openai_client = OpenAI(
                api_key=os.environ['LANGCHECK_OPENAI_API_KEY'])
            openai_args = {'model': os.environ['LANGCHECK_OPENAI_API_MODEL']}
        metric_result = metric_fn(*self.args,
                                  model_type=model_type,
                                  openai_client=openai_client,
                                  openai_args=openai_args)
        return metric_result.metric_values[0], metric_result.explanations[0]

    def compute_metrics_and_update_db(self, language):
        if language not in self.metric_fns:
            return
        if self.local_metric_id is not None:
            value = self.compute_local_metric(language)
            db.update_metric_by_id(value, None, self.local_metric_id)
        if self.openai_metric_id is not None:
            value, explanation = self.compute_openai_metric(language)
            db.update_metric_by_id(value, explanation, self.openai_metric_id)


def get_factual_consistency(response, source,
                            language) -> Tuple[float, Optional[str]]:
    use_local = os.environ['ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True'

    if language == 'ja' and use_local:
        # TODO: Remove this once the problem is fixed in langcheck package
        if len(source) >= 512:
            first_factual_consistency_metric = Metric(
                'factual_consistency', {
                    'en': langcheck.metrics.factual_consistency,
                    'ja': langcheck.metrics.ja.factual_consistency,
                    'de': langcheck.metrics.de.factual_consistency,
                    'zh': langcheck.metrics.zh.factual_consistency
                }, [response, source[:len(source) // 2]], True, False)
            second_factual_consistency_metric = Metric(
                'factual_consistency', {
                    'en': langcheck.metrics.factual_consistency,
                    'ja': langcheck.metrics.ja.factual_consistency,
                    'de': langcheck.metrics.de.factual_consistency,
                    'zh': langcheck.metrics.zh.factual_consistency
                }, [response, source[len(source) // 2:]], True, False)
            first_score = first_factual_consistency_metric.compute_local_metric(
                language)
            second_score = second_factual_consistency_metric.compute_local_metric(
                language)
            return max(first_score, second_score), None

    if use_local:
        factual_consistency_metric = Metric(
            'factual_consistency', {
                'en': langcheck.metrics.factual_consistency,
                'ja': langcheck.metrics.ja.factual_consistency,
                'de': langcheck.metrics.de.factual_consistency,
                'zh': langcheck.metrics.zh.factual_consistency
            }, [response, source], True, False)
        return factual_consistency_metric.compute_local_metric(language), None

    else:
        factual_consistency_metric = Metric(
            'factual_consistency', {
                'en': langcheck.metrics.factual_consistency,
                'ja': langcheck.metrics.ja.factual_consistency,
                'de': langcheck.metrics.de.factual_consistency,
                'zh': langcheck.metrics.zh.factual_consistency
            }, [response, source], False, True)
        return factual_consistency_metric.compute_openai_metric(language)


def main(log_id):
    chatlog = db.get_chatlog_by_id(log_id)
    request = chatlog['request']
    response = chatlog['response']
    source = chatlog['source']
    language = chatlog['language']

    metrics_to_compute = []
    enable_local = os.environ['ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True'
    if enable_local:
        # If the local version of factual consistency was computed first, we
        # need to now compute the OpenAI version
        metrics_to_compute.append(
            Metric(
                'factual_consistency', {
                    'en': langcheck.metrics.factual_consistency,
                    'ja': langcheck.metrics.ja.factual_consistency
                }, [response, source], False, True))
    metrics_to_compute.append(
        Metric(
            'context_relevance', {
                'en': langcheck.metrics.context_relevance,
                'ja': langcheck.metrics.ja.context_relevance
            }, [source, request], False, True))
    metrics_to_compute.append(
        Metric(
            'answer_relevance', {
                'en': langcheck.metrics.answer_relevance,
                'ja': langcheck.metrics.ja.answer_relevance
            }, [response, request], False, True))
    metrics_to_compute.append(
        Metric('request_toxicity', {
            'en': langcheck.metrics.toxicity,
            'ja': langcheck.metrics.ja.toxicity
        }, [request], enable_local, True))
    metrics_to_compute.append(
        Metric('response_toxicity', {
            'en': langcheck.metrics.toxicity,
            'ja': langcheck.metrics.ja.toxicity
        }, [response], enable_local, True))
    metrics_to_compute.append(
        Metric(
            'request_sentiment', {
                'en': langcheck.metrics.sentiment,
                'ja': langcheck.metrics.ja.sentiment
            }, [request], enable_local, True))
    metrics_to_compute.append(
        Metric(
            'response_sentiment', {
                'en': langcheck.metrics.sentiment,
                'ja': langcheck.metrics.ja.sentiment
            }, [response], enable_local, True))
    metrics_to_compute.append(
        Metric('request_fluency', {
            'en': langcheck.metrics.fluency,
            'ja': langcheck.metrics.ja.fluency
        }, [request], enable_local, True))
    metrics_to_compute.append(
        Metric('response_fluency', {
            'en': langcheck.metrics.fluency,
            'ja': langcheck.metrics.ja.fluency
        }, [response], enable_local, True))
    metrics_to_compute.append(
        Metric(
            'request_readability', {
                'en': langcheck.metrics.flesch_reading_ease,
                'ja': langcheck.metrics.ja.tateishi_ono_yamada_reading_ease
            }, [request], True, False))
    metrics_to_compute.append(
        Metric(
            'response_readability', {
                'en': langcheck.metrics.flesch_reading_ease,
                'ja': langcheck.metrics.ja.tateishi_ono_yamada_reading_ease
            }, [response], True, False))
    # TODO: Use japanese metrics once implemented
    metrics_to_compute.append(
        Metric(
            'ai_disclaimer_similarity', {
                'en': langcheck.metrics.ai_disclaimer_similarity,
                'ja': langcheck.metrics.ai_disclaimer_similarity
            }, [response], True, False))

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
    if len(sys.argv) > 1:
        log_id = sys.argv[1]
        main(int(log_id))
