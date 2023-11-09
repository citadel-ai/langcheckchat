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

// Trigger send-button click event when Enter key is pressed
$('#user-input').keypress(function (event) {
  if (event.which == 13) { // 13 is the Enter key's code
    event.preventDefault(); // Prevents default action (like form submission)
    sendMessage();
  }
});

$('[data-toggle="tooltip"]').tooltip({'trigger': 'hover'});

/*************************************************************************
* Event handlers
*************************************************************************/

function sendMessage() {
  const language = $("#language-toggle").val();
  const question = $('#user-input').val();
  if (question.trim() === "") { return; }  // Don't send an empty message


  // Show loading indicator
  $('#metrics-and-sources-container').hide();
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

    // Poll metrics every second
    if (metricsPollingInterval !== undefined) {
      clearInterval(metricsPollingInterval);
    }
    metricsPollingInterval = setInterval(updateMetrics.bind(null, data.id), 1000);
    updateMetrics(data.id);  // So the table isn't empty for 1 second
  });
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

function updateMetrics(id) {
  $.get(`/api/metrics/${id}`)
    .then(function (data) {
      $('#metrics-table tbody').empty();

      for (let metric in data) {
        if (metric !== "completed") {
          let value = data[metric] !== null ? data[metric] : '<div class="spinner-border spinner-border-sm"></div>';
          $('#metrics-table tbody').append(`<tr><td>${metric}</td><td>${round(value, 4)}</td></tr>`);
        }
      }

      if (data.completed) {
        // Stop polling if metrics computation is completed
        clearInterval(metricsPollingInterval);
      }
    });
}

/*************************************************************************
* Utils
*************************************************************************/

// Round a float to even with decimal places
// Rounding logic: https://stackoverflow.com/a/49080858
function round(n, places) {
  if (typeof n !== 'number' || Number.isInteger(n)) { return n; }
  var x = n * Math.pow(10, places);
  var r = Math.round(x);
  // Account for precision using Number.EPSILON
  var br = (Math.abs(x) % 1 > 0.5 - Number.EPSILON && Math.abs(x) % 1 < 0.5 + Number.EPSILON) ? (r % 2 === 0 ? r : r - 1) : r;
  return br / Math.pow(10, places);
}