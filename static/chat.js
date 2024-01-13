/*************************************************************************
* Page setup
*************************************************************************/

let metricsPollingInterval;
let chatEndpoint;
if (document.location.pathname == '/demo') {
  chatEndpoint = '/api/chat_demo'  // Get canned responses to speed up live demos
} else {
  chatEndpoint = '/api/chat'
}

$('#send-button').click(sendMessage);
$('#submit-ref-button').click(calculateReferenceBasedTextQuality);

// Trigger send-button click event when Enter key is pressed
$('#user-input').keypress(function (event) {
  if (event.which == 13) { // 13 is the Enter key's code
    event.preventDefault(); // Prevents default action (like form submission)
    sendMessage();
  }
});
$('#user-ref-input').keypress(function (event) {
  if ($('#submit-ref-button').prop('disabled')) { return; }

  if (event.which == 13) { // 13 is the Enter key's code
    event.preventDefault(); // Prevents default action (like form submission)
    calculateReferenceBasedTextQuality();
  }
});

$('[data-toggle="tooltip"]').tooltip({'trigger': 'hover'});

// Global variable that tracks the current log id
let logID;

/*************************************************************************
* Event handlers
*************************************************************************/

function sendMessage() {
  const language = $("#language-toggle").val();
  const question = $('#user-input').val();
  if (question.trim() === "") { return; }  // Don't send an empty message


  // Show loading indicator
  $('#metrics-and-sources-container').hide();
  $('#reference-input').hide();
  $("#user-ref-input").val('');
  $('#chat-window').empty();
  $('#chat-window').show();
  $('#chat-window').append(`
    <div id="spinner-container" class="text-center">
      <div class="spinner-border text-success my-3" style="width: 5rem; height: 5rem;"></div>
    </div>
  `);

  // Clear metrics
  $('#metrics-table-container tbody').empty();
  $('#sources-table tbody pre').empty();

  // Hide the "Reference-Based Text Quality Metrics" table by default
  $('#reference-based-metrics-container').hide();

  $.post({
    url: chatEndpoint,
    data: JSON.stringify({ message: question, language: language }),
    contentType: 'application/json;charset=UTF-8',
    dataType: 'json',
  }).then(function (data) {
    // Append the bot's answer
    $('#metrics-and-sources-container').show();
    $('#spinner-container').remove();
    $('#reference-input').show();
    $('#submit-ref-button').prop('disabled', true);
    $('#submit-ref-button').tooltip({'trigger': 'hover'});
    $('#chat-window').append(generateAnswerRow(data.response, data.score, data.warning));
    $('#sources-table tbody pre').text(data.source);
    $('[data-toggle="tooltip"]').tooltip({'trigger': 'hover'});

    // Save the log_id into the global variable
    logID = data.id;

    // Poll metrics every second
    if (metricsPollingInterval !== undefined) {
      clearInterval(metricsPollingInterval);
    }
    metricsPollingInterval = setInterval(updateMetrics.bind(null, logID), 1000);
    updateMetrics(logID);  // So the table isn't empty for 1 second
  });
}

function calculateReferenceBasedTextQuality(e) {
  const reference = $('#user-ref-input').val();
  if (reference.trim() === "") { return; }  // Don't send an empty message

  // Scroll to the metrics table
  scrollToMetricsTable(e)

  $.post({
    url: '/api/ref_metric',
    data: JSON.stringify({ log_id: logID, reference: reference }),
    contentType: 'application/json;charset=UTF-8',
    dataType: 'json',
  }).then(function () {
    // Poll metrics every second
    if (metricsPollingInterval !== undefined) {
      clearInterval(metricsPollingInterval);
    }
    metricsPollingInterval = setInterval(updateMetrics.bind(null, logID), 1000);
    updateMetrics(logID);  // So the table isn't empty for 1 second
  });
}

function scrollToMetricsTable(e) {
  var tableTop = $('#metrics-table-container').offset().top;
  $('html, body').animate({scrollTop: tableTop}, 500);
}

function generateAnswerRow(answer, factualConsistencyScore, warning) {
  let warning_text = '';
  if (warning) {
    warning_text = '<div class="text-danger mb-4">Warning: possible hallucination detected.</div>'
  }

  return `
    <div class="qa-block">
      ${warning_text}
      <span class="text-success" style="font-weight: 500;">Answer: </span>
      ${answer}
      <br>
      ${
        warning
        ?
        `<a class="badge badge-danger mt-4" href="https://langcheck.readthedocs.io/en/latest/langcheck.metrics.en.source_based_text_quality.html#langcheck.metrics.en.source_based_text_quality.factual_consistency" target="_blank" data-toggle="tooltip" data-placement="right" title="This is the factual consistency between the LLM's answer and the source document. Click to open the LangCheck documentation.">
          Factual Consistency Score: ${round(factualConsistencyScore, 4)}
        </a>`
        :
        `<a class="badge badge-success mt-4" href="https://langcheck.readthedocs.io/en/latest/langcheck.metrics.en.source_based_text_quality.html#langcheck.metrics.en.source_based_text_quality.factual_consistency" target="_blank" data-toggle="tooltip" data-placement="right" title="This is the factual consistency between the LLM's answer and the source document. Click to open the LangCheck documentation.">
          Factual Consistency Score: ${round(factualConsistencyScore, 4)}
        </a>`
      }
    </div>
  `;
}

const METRICS_WITH_EXPLANATION = [
  'request_fluency_openai',
  'request_sentiment_openai',
  'request_toxicity_openai',
  'response_fluency_openai',
  'response_sentiment_openai',
  'response_toxicity_openai',
  'factual_consistency_openai'
];

const REFERENCE_FREE_METRICS = [
  'request_toxicity',
  'request_toxicity_openai',
  'response_toxicity',
  'response_toxicity_openai',
  'request_sentiment',
  'request_sentiment_openai',
  'response_sentiment',
  'response_sentiment_openai',
  'request_fluency',
  'request_fluency_openai',
  'response_fluency',
  'response_fluency_openai',
  'request_readability',
  'response_readability',
  'ai_disclaimer_similarity'
];

const SOURCE_BASED_METRICS = [
  'factual_consistency',
  'factual_consistency_openai'
];

const REFERENCE_BASED_METRICS = [
  'rouge1',
  'rouge2',
  'rougeL',
  'semantic_similarity'
];
function updateMetrics(id) {
  $.get(`/api/metrics/${id}`)
    .then(function (data) {
      $('#metrics-table-container tbody').empty();
      // Add a row with a spinner if the status is still "new"
      if (data.status === 'new') {
        $('#metrics-table-container tbody').append(`<tr><td colspan="2" style="text-align: center;"><div class="spinner-border spinner-border-sm"></div></td></tr>`);
        return;
      }
      for (let metricName in data) {
        if (metricName === "status") {
          continue;
        }
        let value = data[metricName]['metric_value'] !== null ? data[metricName]['metric_value'] : '<div class="spinner-border spinner-border-sm"></div>';
        let metricTableID = ''
        if (REFERENCE_FREE_METRICS.includes(metricName)) {
          metricTableID = '#reference-free-metrics-table';
        } else if (SOURCE_BASED_METRICS.includes(metricName)) {
          metricTableID = '#source-based-metrics-table';
        } else if (REFERENCE_BASED_METRICS.includes(metricName)) {
          metricTableID = '#referebce-based-metrics-table';
          $('#reference-based-metrics-container').show();
        }
        if (METRICS_WITH_EXPLANATION.includes(metricName)) {
          $(metricTableID + ' tbody').append(`<tr><td id=${metricName}>${metricName}<span class="ml-2 d-none" data-feather="help-circle" data-toggle="tooltip" data-placement="top"></td><td>${round(value, 4)}</td></tr>`);
        } else {
          $(metricTableID + ' tbody').append(`<tr><td>${metricName}</td><td>${round(value, 4)}</td></tr>`);
        }
      }

      if (data.status === 'done') {
        // Add OpenAI metrics explanation
        getMetricsExplanation(id);
        // Stop polling if metrics computation is done
        clearInterval(metricsPollingInterval);
        // Remove the loading indicators, if any
        $('#metrics-table-container .spinner-border').remove();
        // Enable the "Submit Reference" button
        $('#submit-ref-button').prop("disabled", false);
        // Hide the tooktip for the "Submit Reference" button
        $('#submit-ref-button').tooltip('dispose');
      }
    });
}

function getMetricsExplanation(id) {
  // Add the metric explanation tooltips
  $.get(`/api/metrics/${id}`)
  .then(function (data) {
    for (const metric in data) {
      if(metric.endsWith('_openai')) {
        $(`#${metric} svg`).attr('data-original-title', data[metric]['explanation']);
        $('#metrics-table-container tbody svg').removeClass("d-none");
        $('#metrics-table-container [data-toggle="tooltip"]').tooltip({'trigger': 'hover'});
      }
    }
  });
  feather.replace();
}
