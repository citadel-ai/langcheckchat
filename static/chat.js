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

  // Show the "Reference-Based Text Quality Metrics" table
  $('#reference-based-metrics-container').show();

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
        let metricTableID = ''
        if (Object.keys(REFERENCE_FREE_METRICS).includes(metricName)) {
          metricTableID = '#reference-free-metrics-table';
        } else if (Object.keys(SOURCE_BASED_METRICS).includes(metricName)) {
          metricTableID = '#source-based-metrics-table';
        } else if (Object.keys(REFERENCE_BASED_METRICS).includes(metricName)) {
          metricTableID = '#reference-based-metrics-table';
        } else {
          continue;
        }
        // Add a header cell for the metrics table
        let metricRowHTML = (data[metricName]['explanation'] !== null) ? 
          `<tr>
            <td id=${metricName}>${metricName}
              <span class="ml-2 d-none" data-html="true" data-toggle="tooltip" data-placement="top">
                <span data-feather="help-circle"></span>
              </span>
            </td>` : 
          `<tr><td>${metricName}</td>`;

        // Add a data cell for the metrics table
        if (data[metricName]['metric_value'] !== null) {
          if (thresholdExceeded(metricName, data[metricName]['metric_value'])) {
              metricRowHTML += `<td class="bg-danger text-white">${round(data[metricName]['metric_value'], 4)}</td></tr>`;
          } else {
            metricRowHTML += `<td>${round(data[metricName]['metric_value'], 4)}</td></tr>`;
          }
        } else {
          metricRowHTML += `<td><div class="spinner-border spinner-border-sm"></div></td></tr>`;
        }
        $(metricTableID + ' tbody').append(metricRowHTML)
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
        const title = escapeHTML(data[metric]['explanation']);
        $(`#${metric} span[data-toggle="tooltip"]`).attr('data-original-title', title);
        $('#metrics-table-container tbody span[data-toggle="tooltip"]').removeClass("d-none");
      }
    }
  });
  feather.replace();
  $('[data-toggle="tooltip"]').tooltip();
}
