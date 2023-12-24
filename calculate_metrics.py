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
            response, source, model_type='azure_openai', openai_args=openai_args)
        # TODO: Gracefully handle the case where the score is None
        assert factual_consistency.metric_values[0] is not None
        # For type check
        assert factual_consistency.explanations is not None
        return factual_consistency.metric_values[
            0], factual_consistency.explanations[0]
    else:
        assert not use_local and language == 'en'
        factual_consistency = langcheck.metrics.factual_consistency(
            response, source, model_type='azure_openai', openai_args=openai_args)
        # TODO: Gracefully handle the case where the score is None
        assert factual_consistency.metric_values[0] is not None
        # For type check
        assert factual_consistency.explanations is not None
        return factual_consistency.metric_values[
            0], factual_consistency.explanations[0]


def add_reference_based_metrics_to_db(log_id: int, reference: str):
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
                         [response, reference, request], 'semantic_similarity', log_id)
    else:
        add_metric_to_db(langcheck.metrics.ja.rouge1,
                         [response, reference, request], 'rouge1', log_id)
        add_metric_to_db(langcheck.metrics.ja.rouge2,
                         [response, reference, request], 'rouge2', log_id)
        add_metric_to_db(langcheck.metrics.ja.rougeL,
                         [response, reference, request], 'rougeL', log_id)
        add_metric_to_db(langcheck.metrics.ja.semantic_similarity,
                         [response, reference, request], 'semantic_similarity', log_id)
    db.update_chatlog_by_id({'completed': 1}, log_id)


def add_init_to_db(request, response, source, language, score, explanation,
                   timestamp) -> int:
    if os.environ['ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True':
        log_id = db.insert_chatlog({
            'request': request, 'response': response, 'source': source, 'language': language,
            'factual_consistency': score, 'timestamp': timestamp
        })
    else:
        log_id = db.insert_chatlog({
            'request': request, 'response': response, 'source': source, 'language': language,
            'factual_consistency_openai': score, 'factual_consistency_openai_explanation': explanation,
            'timestamp': timestamp
        })
    # For type check
    assert log_id is not None
    return log_id


def add_metric_to_db(metric_fn,
                     metric_args,
                     name,
                     log_id,
                     openai_args=None):
    # Calculate the local metric if local metrics are enabled or if this metric
    # does not have an OpenAI version
    if os.environ[
            'ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True' or openai_args is None:
        metric_value = metric_fn(*metric_args)
        db.update_chatlog_by_id(
            {name: metric_value.metric_values[0]}, log_id)
    if openai_args:
        metric_value_openai = metric_fn(*metric_args,
                                        model_type='azure_openai',
                                        openai_args=openai_args)
        db.update_chatlog_by_id(
            {f"{name}_openai": metric_value_openai.metric_values[0],
             f"{name}_openai_explanation": metric_value_openai.explanations[0]}, log_id)


def main(log_id):
    chatlog = db.get_chatlog_by_id(log_id)
    request = chatlog['request']
    response = chatlog['response']
    source = chatlog['source']
    language = chatlog['language']

    openai_args = {'model': os.environ['AZURE_OPENAI_API_DEPLOYMENT']}
    if language == 'en':
        if os.environ['ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True':
            # If the local version of factual consistency was computed
            # first, we compute the OpenAI version here
            factual_consistency_openai = langcheck.metrics.factual_consistency(
                response,
                source,
                model_type='azure_openai',
                openai_args=openai_args)
            db.update_chatlog_by_id(
                {'factual_consistency_openai': factual_consistency_openai.metric_values[0],
                 'factual_consistency_openai_explanation': factual_consistency_openai.explanations[0]
                 }, log_id)
        add_metric_to_db(langcheck.metrics.toxicity, [request],
                         'request_toxicity',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.sentiment, [request],
                         'request_sentiment',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.fluency, [request],
                         'request_fluency',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.flesch_reading_ease,
                         [request], 'request_readability', log_id)

        add_metric_to_db(langcheck.metrics.toxicity, [response],
                         'response_toxicity',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.sentiment, [response],
                         'response_sentiment',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.fluency, [response],
                         'response_fluency',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.flesch_reading_ease,
                         [response], 'response_readability', log_id)
        add_metric_to_db(langcheck.metrics.ai_disclaimer_similarity,
                         [response], 'ai_disclaimer_similarity', log_id)
    else:
        if os.environ['ENABLE_LOCAL_LANGCHECK_MODELS'] == 'True':
            # If the local version of factual consistency was computed
            # first, we compute the OpenAI version here
            factual_consistency_openai = langcheck.metrics.ja.factual_consistency(
                response,
                source,
                model_type='azure_openai',
                openai_args=openai_args)
            db.update_chatlog_by_id(
                {'factual_consistency_openai': factual_consistency_openai.metric_values[0],
                 'factual_consistency_openai_explanation': factual_consistency_openai.explanations[0]},
                log_id)
        add_metric_to_db(langcheck.metrics.ja.toxicity, [request],
                         'request_toxicity',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.ja.sentiment, [request],
                         'request_sentiment',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.ja.fluency, [request],
                         'request_fluency',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.ja.tateishi_ono_yamada_reading_ease,
                         [request], 'request_readability', log_id)

        add_metric_to_db(langcheck.metrics.ja.toxicity, [response],
                         'response_toxicity',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.ja.sentiment, [response],
                         'response_sentiment',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.ja.fluency, [response],
                         'response_fluency',
                         log_id,
                         openai_args=openai_args)
        add_metric_to_db(langcheck.metrics.ja.tateishi_ono_yamada_reading_ease,
                         [response], 'response_readability', log_id)
        # TODO: Use japanese metrics once implemented
        add_metric_to_db(langcheck.metrics.ai_disclaimer_similarity,
                         [response], 'ai_disclaimer_similarity', log_id)
    db.update_chatlog_by_id({'completed': 1}, log_id)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        log_id = sys.argv[1]
        main(int(log_id))