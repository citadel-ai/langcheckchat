const REFERENCE_FREE_METRICS = {
  'request_toxicity': { threshold: 0.5, direction: 'low'},
  'request_toxicity_openai': { threshold: 0.5, direction: 'low'},
  'response_toxicity': { threshold: 0.5, direction: 'low'},
  'response_toxicity_openai': { threshold: 0.5, direction: 'low'},
  'request_sentiment': { threshold: 0.5, direction: 'high'},
  'request_sentiment_openai': { threshold: 0.5, direction: 'high'},
  'response_sentiment': { threshold: 0.5, direction: 'high'},
  'response_sentiment_openai': { threshold: 0.5, direction: 'high'},
  'request_fluency': { threshold: 0.5, direction: 'high'},
  'request_fluency_openai': { threshold: 0.5, direction: 'high'},
  'response_fluency': { threshold: 0.5, direction: 'high'},
  'response_fluency_openai': { threshold: 0.5, direction: 'high'},
  'request_readability': { threshold: null, direction: null},
  'response_readability': { threshold: null, direction: null},
  'ai_disclaimer_similarity': { threshold: 0.5, direction: 'low'},
  'answer_relevance_openai': { threshold: 0.5, direction: 'high'},
};

const SOURCE_BASED_METRICS = {
  'factual_consistency': { threshold: 0.5, direction: 'high'},
  'factual_consistency_openai': { threshold: 0.5, direction: 'high'},
  'context_relevance_openai': { threshold: 0.5, direction: 'high'},
};

const REFERENCE_BASED_METRICS = {
  'rouge1': { threshold: 0.5, direction: 'high'},
  'rouge2': { threshold: 0.5, direction: 'high'},
  'rougeL': { threshold: 0.5, direction: 'high'},
  'semantic_similarity': { threshold: 0.5, direction: 'high'},
};

function thresholdExceeded(metricName, metricValue) {
  let metricInfo = {};
  if (Object.keys(REFERENCE_FREE_METRICS).includes(metricName)) {
    metricInfo = REFERENCE_FREE_METRICS[metricName];
  } else if (Object.keys(SOURCE_BASED_METRICS).includes(metricName)) {
    metricInfo = SOURCE_BASED_METRICS[metricName];
  } else if (Object.keys(REFERENCE_BASED_METRICS).includes(metricName)) {
    metricInfo = REFERENCE_BASED_METRICS[metricName];
  } else {
    return false
  }
  if ((metricInfo.direction === 'low' && metricValue > metricInfo.threshold) ||
    (metricInfo.direction === 'high' && metricValue < metricInfo.threshold)) {
    return true
  }
  return false
}
