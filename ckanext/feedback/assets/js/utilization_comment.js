window.addEventListener('pageshow', (event) => {
  if (event.persisted || performance.getEntriesByType("navigation")[0]?.type === "back_forward") {
    if (sessionStorage.getItem('is_suggestion') === 'true') {
      const utilizationId = document.getElementById('utilization-id').value;
      const inputComment = sessionStorage.getItem('input-comment');
      const suggestedComment = sessionStorage.getItem('suggested-comment');

      postPreviousSuggestedLog(utilizationId, inputComment, suggestedComment);
    }
  }
});

function postPreviousSuggestedLog(utilizationId, inputComment, suggestedComment) {
  fetch('/utilization/' + utilizationId + '/comment/create_previous_suggestion_log', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      'input_comment': inputComment,
      'suggested_comment': suggestedComment,
    })
  });

  sessionStorage.removeItem('input-comment');
  sessionStorage.removeItem('suggested-comment');

  return;
}
