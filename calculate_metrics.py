import os
import sys
from typing import Optional, Tuple

import langcheck.metrics
from dotenv import load_dotenv

import database as db

load_dotenv()


def get_factual_consistency_score(
        source: str, response: str,
        language: str) -> Tuple[float, Optional[str]]:
    '''Get factual consistency score for a response given a source.'''
    openai_args = {'model': os.environ['AZURE_OPENAI_API_DEPLOYMENT']}
    use_local = os.environ['ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True'
    if use_local and language == 'ja':
        # TODO: Remove this once the problem is fixed in langcheck package
        if len(source) < 512:
            factual_consistency_score = langcheck.metrics.ja.factual_consistency(
                response, source).metric_values[0]
        else:
            factual_consistency_score_fst = langcheck.metrics.ja.factual_consistency(
                response, source[:len(source) // 2]).metric_values[0]
            factual_consistency_score_snd = langcheck.metrics.ja.factual_consistency(
                response, source[len(source) // 2:]).metric_values[0]
            # For type check
            assert factual_consistency_score_fst is not None
            assert factual_consistency_score_snd is not None
            factual_consistency_score = max(factual_consistency_score_fst,
                                            factual_consistency_score_snd)
        # For type check
        assert factual_consistency_score is not None
        return factual_consistency_score, None

    elif use_local and language == 'en':
        factual_consistency_score = langcheck.metrics.factual_consistency(
            response, source).metric_values[0]
        # For type check
        assert factual_consistency_score is not None
        return factual_consistency_score, None

    elif not use_local and language == 'ja':
        factual_consistency = langcheck.metrics.ja.factual_consistency(
            response,
            source,
            model_type='azure_openai',
            openai_args=openai_args)
        # TODO: Gracefully handle the case where the score is None
        assert factual_consistency.metric_values[0] is not None
        # For type check
        assert factual_consistency.explanations is not None
        return factual_consistency.metric_values[
            0], factual_consistency.explanations[0]
    else:
        assert not use_local and language == 'en'
        factual_consistency = langcheck.metrics.factual_consistency(
            response,
            source,
            model_type='azure_openai',
            openai_args=openai_args)
        # TODO: Gracefully handle the case where the score is None
        assert factual_consistency.metric_values[0] is not None
        # For type check
        assert factual_consistency.explanations is not None
        return factual_consistency.metric_values[
            0], factual_consistency.explanations[0]


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


def add_metric_to_db(metric_fn, metric_args, name, log_id, openai_args=None):
    # Calculate the local metric if local metrics are enabled or if this metric
    # does not have an OpenAI version
    if os.environ[
            'ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True' or openai_args is None:
        metric_value = metric_fn(*metric_args)
        db.insert_metric(log_id, name, metric_value.metric_values[0], None)
    if openai_args:
        metric_value_openai = metric_fn(*metric_args,
                                        model_type='azure_openai',
                                        openai_args=openai_args)
        db.insert_metric(log_id, f"{name}_openai",
                         metric_value_openai.metric_values[0],
                         metric_value_openai.explanations[0])


def main(log_id):
    chatlog = db.get_chatlog_by_id(log_id)
    request = chatlog['request']
    response = chatlog['response']
    source = chatlog['source']
    language = chatlog['language']

    openai_args = {'model': os.environ['AZURE_OPENAI_API_DEPLOYMENT']}
    metrics_to_compute = [
        {
            'metric_fn': langcheck.metrics.toxicity,
            'metric_fn_jp': langcheck.metrics.ja.toxicity,
            'name': 'toxicity',
            'compute_on': ['request', 'response'],
            'has_openai': True
        },
        {
            'metric_fn': langcheck.metrics.sentiment,
            'metric_fn_jp': langcheck.metrics.ja.sentiment,
            'name': 'sentiment',
            'compute_on': ['request', 'response'],
            'has_openai': True
        },
        {
            'metric_fn': langcheck.metrics.fluency,
            'metric_fn_jp': langcheck.metrics.ja.fluency,
            'name': 'fluency',
            'compute_on': ['request', 'response'],
            'has_openai': True
        },
        {
            'metric_fn': langcheck.metrics.flesch_reading_ease,
            'metric_fn_jp':
            langcheck.metrics.ja.tateishi_ono_yamada_reading_ease,
            'name': 'readability',
            'compute_on': ['request', 'response'],
            'has_openai': False
        },
        {
            'metric_fn': langcheck.metrics.ai_disclaimer_similarity,
            # TODO: Use japanese metrics once implemented
            'metric_fn_jp': langcheck.metrics.ai_disclaimer_similarity,
            'name': 'ai_disclaimer_similarity',
            'compute_on': ['response'],
            'has_openai': False
        }
    ]
    if language == 'en':
        if os.environ['ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True':
            # If the local version of factual consistency was computed
            # first, we compute the OpenAI version here
            factual_consistency_openai = langcheck.metrics.factual_consistency(
                response,
                source,
                model_type='azure_openai',
                openai_args=openai_args)
            db.insert_metric(log_id, 'factual_consistency_openai',
                             factual_consistency_openai.metric_values[0],
                             factual_consistency_openai.explanations[0])
        for metric in metrics_to_compute:
            for metric_arg in metric['compute_on']:
                metric_name = f"{metric['name']}_{metric_arg}"
                if metric['has_openai']:
                    add_metric_to_db(metric['metric_fn'],
                                     [chatlog[metric_arg]],
                                     metric_name,
                                     log_id,
                                     openai_args=openai_args)
                else:
                    add_metric_to_db(metric['metric_fn'],
                                     [chatlog[metric_arg]], metric_name,
                                     log_id)
    else:
        if os.environ['ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True':
            # If the local version of factual consistency was computed
            # first, we compute the OpenAI version here
            factual_consistency_openai = langcheck.metrics.ja.factual_consistency(
                response,
                source,
                model_type='azure_openai',
                openai_args=openai_args)
            db.insert_metric(log_id, 'factual_consistency_openai',
                             factual_consistency_openai.metric_values[0],
                             factual_consistency_openai.explanations[0])
        for metric in metrics_to_compute:
            for metric_arg in metric['compute_on']:
                metric_name = f"{metric['name']}_{metric_arg}"
                if metric['has_openai']:
                    add_metric_to_db(metric['metric_fn_jp'],
                                     [chatlog[metric_arg]],
                                     metric_name,
                                     log_id,
                                     openai_args=openai_args)
                else:
                    add_metric_to_db(metric['metric_fn_jp'],
                                     [chatlog[metric_arg]], metric_name,
                                     log_id)
    db.update_chatlog_by_id({'completed': 1}, log_id)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        log_id = sys.argv[1]
        main(int(log_id))
