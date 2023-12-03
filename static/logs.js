let currentPage = 1;

function loadLogs(direction) {
    if (direction === 'next') {
        currentPage += 1;
    } else if (direction === 'prev' && currentPage > 1) {
        currentPage -= 1;
    }
    $('#qa-table tr:not(:first)').remove();  // Remove all rows except headers
    $.get('/api/logs?page=' + currentPage, function(data) {
        data.logs.forEach(log => {
            $('#qa-table').append(
                `<tr>
                    <td>${log.request}</td>
                    <td>${log.response}</td>
                    <td>
                        <table class="table table-bordered table-hover" id="metrics-table">
                            <thead class="thead-light">
                                <tr>
                                    <th>Metric</th>
                                    <th>Value</th>
                                </tr>
                                </thead>
                            <tbody class="text-monospace">
                                <tr><td>request_toxicity</td><td>${round(log.request_toxicity, 4)}</td></tr>
                                <tr>
                                    <td class="d-flex align-items-center">
                                        <span>request_toxicity_openai</span>
                                        <span class="ml-2" data-feather="help-circle" data-toggle="tooltip" data-placement="top" title="${log.request_toxicity_openai_explanation.replace(/"/g, "'")}">
                                    </td>
                                    <td>${round(log.request_toxicity_openai, 4)}</td></tr>
                                <tr><td>request_sentiment</td><td>${round(log.request_sentiment, 4)}</td></tr>
                                <tr>
                                    <td class="d-flex align-items-center">
                                        <span>request_sentiment_openai</span>
                                        <span class="ml-2" data-feather="help-circle" data-toggle="tooltip" data-placement="top" title="${log.request_sentiment_openai_explanation.replace(/"/g, "'")}">
                                    </td>
                                    <td>${round(log.request_sentiment_openai, 4)}</td>
                                </tr>
                                <tr><td>request_fluency</td><td>${round(log.request_fluency, 4)}</td></tr>
                                <tr>
                                    <td class="d-flex align-items-center">
                                        <span>request_fluency_openai</span>
                                        <span class="ml-2" data-feather="help-circle" data-toggle="tooltip" data-placement="top" title="${log.request_fluency_openai_explanation.replace(/"/g, "'")}">
                                    </td>
                                    <td>${round(log.request_fluency_openai, 4)}</td>
                                </tr>
                                <tr><td>response_toxicity</td><td>${round(log.response_toxicity, 4)}</td></tr>
                                <tr>
                                    <td class="d-flex align-items-center">
                                        <span>response_toxicity_openai</span>
                                        <span class="ml-2" data-feather="help-circle" data-toggle="tooltip" data-placement="top" title="${log.response_toxicity_openai_explanation.replace(/"/g, "'")}">
                                    </td>
                                    <td>${round(log.response_toxicity_openai, 4)}</td>
                                </tr>
                                <tr><td>response_sentiment</td><td>${round(log.response_sentiment, 4)}</td></tr>
                                <tr>
                                    <td class="d-flex align-items-center">
                                        <span>response_sentiment_openai</span>
                                        <span class="ml-2" data-feather="help-circle" data-toggle="tooltip" data-placement="top" title="${log.response_sentiment_openai_explanation.replace(/"/g, "'")}">
                                    </td>
                                    <td>${round(log.response_sentiment_openai, 4)}</td>
                                </tr>
                                <tr><td>response_fluency</td><td>${round(log.response_fluency, 4)}</td></tr>
                                <tr>
                                    <td class="d-flex align-items-center">
                                        <span>response_fluency_openai</span>
                                        <span class="ml-2" data-feather="help-circle" data-toggle="tooltip" data-placement="top" title="${log.response_fluency_openai_explanation.replace(/"/g, "'")}">
                                    </td>
                                    <td>${round(log.response_fluency_openai, 4)}</td>
                                </tr>
                                <tr><td>response_readability</td><td>${round(log.response_readability, 4)}</td></tr>
                                <tr><td>ai_disclaimer_similarity</td><td>${round(log.ai_disclaimer_similarity, 4)}</td></tr>
                                <tr><td>factual_consistency</td><td>${round(log.factual_consistency, 4)}</td></tr>
                                <tr>
                                    <td class="d-flex align-items-center">
                                        <span>factual_consistency_openai</span>
                                        <span class="ml-2" data-feather="help-circle" data-toggle="tooltip" data-placement="top" title="${log.factual_consistency_openai_explanation.replace(/"/g, "'")}">
                                    </td>
                                    <td>${round(log.factual_consistency_openai, 4)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                    <td>
                        <div class="d-flex justify-content-between">
                            <span class="input-preview">${log.source.substring(0, 300)}...</span>
                            <a href="#" class="show-source ml-2">Show <span data-feather="maximize-2"></span></a>
                        </div>
                        <div style="display: none; white-space: pre-wrap;">${log.source}</div>
                    </td>
                </tr>`
            );
        });
        $('#pageIndicator').text(currentPage);
        feather.replace();
        $('[data-toggle="tooltip"]').tooltip();
    }, 'json');
}

$(document).ready(function() {
    loadLogs(); // Load initial logs on page load
    $('#prevButton').click(function() { loadLogs('prev'); });
    $('#nextButton').click(function() { loadLogs('next'); });
});

$('body').on('click', '.show-source', showSource);
function showSource(e) {
  var link = $(e.currentTarget);
  var input_preview = link.prev();
  var source = link.parent().next();

  if (link.text() === 'Show ') {
    input_preview.css('visibility', 'hidden');
    input_preview.css('height', '0px');
    source.show();
    link.html('Hide ' + feather.icons['minimize-2'].toSvg());
  } else {
    input_preview.css('visibility', 'visible');
    source.hide();
    link.html('Show ' + feather.icons['maximize-2'].toSvg());
  }
  e.preventDefault();
}