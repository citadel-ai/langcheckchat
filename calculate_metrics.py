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


def add_metrics_to_db(metrics_to_compute, chatlog, log_id):
    openai_args = {'model': os.environ['AZURE_OPENAI_API_DEPLOYMENT']}

    # Map the metric id to the callable `metric_fn(chatlog[metric_arg])` or
    # `metric_fn(chatlog[metric_arg], model_type='azure_openai',
    # openai_args=openai_args)` so that we can compute the metric later
    id_to_metric_fn = {}
    for metric_dict in metrics_to_compute:
        # Calculate the local metric if local metrics are enabled or if this metric
        # does not have an OpenAI version
        compute_local = os.environ[
            'ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True' or not metric_dict[
                'has_openai']

        # Use the correct metric function depending on the language
        if chatlog['language'] == 'en':
            metric_fn = metric_dict['metric_fn']
        else:
            metric_fn = metric_dict['metric_fn_jp']

        # First, add the metric name(s) to the database, but don't yet compute
        # the metric
        for metric_arg in metric_dict['compute_on']:
            metric_name = f"{metric_arg}_{metric_dict['name']}"
            if compute_local:
                id = db.insert_metric(log_id, metric_name, None, None)
                id_to_metric_fn[id] = {
                    'fn': metric_fn,
                    'args': [chatlog[metric_arg]]
                }

            if metric_dict['has_openai']:
                metric_name_openai = f"{metric_name}_openai"
                id = db.insert_metric(log_id, metric_name_openai, None, None)
                id_to_metric_fn[id] = {
                    'fn': metric_fn,
                    'args': [chatlog[metric_arg]],
                    'kwargs': {
                        'model_type': 'azure_openai',
                        'openai_args': openai_args
                    }
                }

    # Compute the metrics
    for id, metric_fn in id_to_metric_fn.items():
        fn = metric_fn['fn']
        args = metric_fn['args']
        if 'kwargs' in metric_fn:
            kwargs = metric_fn['kwargs']
            metric_result = fn(*args, **kwargs)
        else:
            metric_result = fn(*args)
        if metric_result is not None:
            metric_value = metric_result.metric_values[0]
            if metric_result.explanations is not None:
                explanation = metric_result.explanations[0]
            else:
                explanation = None
            db.update_metric_by_id(metric_value, explanation, id)


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
        add_metrics_to_db(metrics_to_compute, chatlog, log_id)
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
        add_metrics_to_db(metrics_to_compute, chatlog, log_id)
    db.update_chatlog_by_id({'completed': 1}, log_id)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        log_id = sys.argv[1]
        main(int(log_id))
