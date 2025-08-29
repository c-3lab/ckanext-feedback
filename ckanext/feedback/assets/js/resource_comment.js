window.addEventListener('pageshow', (event) => {
  if (event.persisted || performance.getEntriesByType("navigation")[0]?.type === "back_forward") {
    if (sessionStorage.getItem('is_suggestion') === 'true') {
      const resourceId = document.getElementById('resource-id').value;
      const inputComment = sessionStorage.getItem('input-comment');
      const suggestedComment = sessionStorage.getItem('suggested-comment');

      postPreviousSuggestedLog(resourceId, inputComment, suggestedComment);
    }
  }
});

function postPreviousSuggestedLog(resourceId, inputComment, suggestedComment) {
  fetch('/resource_comment/' + resourceId + '/comment/create_previous_suggestion_log', {
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
