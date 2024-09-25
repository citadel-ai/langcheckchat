/*************************************************************************
* Page setup
*************************************************************************/

let metricsPollingInterval;
let chatEndpoint = '/api/chat'

$('#send-button').click(sendMessage);


$('[data-toggle="tooltip"]').tooltip({'trigger': 'hover'});

// Global variable that tracks the current log id
let logID;

/*************************************************************************
* Event handlers
*************************************************************************/

function sendMessage() {
  const lv = $("#lv-toggle").val();
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
    data: JSON.stringify({ message: question, lv: lv}),
    contentType: 'application/json;charset=UTF-8',
    dataType: 'json',
  }).then(function (data) {
    // Append the bot's answer
    $('#metrics-and-sources-container').show();
    $('#spinner-container').remove();
    $('#reference-input').show();
    $('#submit-ref-button').prop('disabled', true);
    $('#submit-ref-button').tooltip({'trigger': 'hover'});
    console.log(data.response);
    $('#chat-window').append(generateAnswerRow(data.response));

  });
}


function generateAnswerRow(answer) {
  // Convert Markdown to HTML, since OpenAI's answers are often in Markdown
  // format
  const answerHtml = marked.parse(answer);

  return `
    <div class="qa-block">
      <span class="text-success" style="font-weight: 500;">回答: </span>
      ${answerHtml}
    </div>
  `;
}