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
  $('#chat-window').empty();
  $('#chat-window').show();
  $('#chat-window').append(`
    <div id="spinner-container" class="text-center">
      <div class="spinner-border text-success my-3" style="width: 5rem; height: 5rem;"></div>
    </div>
  `);

  // Clear metrics
  $('#metrics-table tbody').empty();
  $('#sources-table tbody pre').empty();

  $.post({
    url: chatEndpoint,
    data: JSON.stringify({ message: question, language: language }),
    contentType: 'application/json;charset=UTF-8',
    dataType: 'json',
  }).then(function (data) {
    // Append the bot's answer
    $('#metrics-and-sources-container').show();
    $('#spinner-container').remove();
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
  const question = $('#user-input').val();
  if (question.trim() === "") { return; }  // Don't send an empty message

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
    metricsPollingInterval = setInterval(updateMetrics.bind(null, logID, true), 1000);
    updateMetrics(logID, true);  // So the table isn't empty for 1 second
  });
}

function scrollToMetricsTable(e) {
  var tableTop = $('#metrics-table').offset().top;
  $('html, body').animate({scrollTop: tableTop}, 500);

  e.preventDefault();
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

const REFERENCE_BASED_METRICS = [
  'rouge1',
  'rouge2',
  'rougeL',
  'semantic_similarity'
];
function updateMetrics(id, refBasedMetricsFlag) {
  $.get(`/api/metrics/${id}`)
    .then(function (data) {
      $('#metrics-table tbody').empty();
      for (let metric in data) {
        if (metric !== "completed" && !metric.endsWith('_explanation')) {
          let value = data[metric] !== null ? data[metric] : '<div class="spinner-border spinner-border-sm"></div>';
          if (METRICS_WITH_EXPLANATION.includes(metric)) {
            $('#metrics-table tbody').append(`<tr><td id=${metric}>${metric}<span class="ml-2 d-none" data-feather="help-circle" data-toggle="tooltip" data-placement="top"></td><td>${round(value, 4)}</td></tr>`);
          } else if(refBasedMetricsFlag || !REFERENCE_BASED_METRICS.includes(metric)) {
            $('#metrics-table tbody').append(`<tr><td>${metric}</td><td>${round(value, 4)}</td></tr>`);
          }
        }
      }

      if (data.completed) {
        // Add OpenAI metrics explanation
        getMetricsExplanation(id);
        // Show the reference text input
        $('#reference-input').show();
        // Stop polling if metrics computation is completed
        clearInterval(metricsPollingInterval);
      }
    });
}

function getMetricsExplanation(id) {
  // Add the metric explanation tooltips
  $.get(`/api/metrics/${id}`)
  .then(function (data) {
    for (const metric in data) {
      if(metric.endsWith('_openai')) {
        $(`#${metric} svg`).attr('data-original-title', data[metric + '_explanation']);
        $('#metrics-table tbody svg').removeClass("d-none");
        $('[data-toggle="tooltip"]').tooltip({'trigger': 'hover'});
      }
    }
  });
  feather.replace();
}
