window.addEventListener('pageshow', (event) => {
  if (isHistory(event)) {
		previousLog();
	}
	updateSessionStorage();
});

function isHistory(event) {
	const navigationType = performance.getEntriesByType("navigation")[0]?.type;
  const isHistory = event.persisted || navigationType === "back_forward";

  return isHistory;
}

function previousLog() {
	const previousType = sessionStorage.getItem('current-type');
	const currentType = document.getElementById('current-type').value;
	const url = createUrl();
	const inputComment = sessionStorage.getItem('input-comment');
	const suggestedComment = sessionStorage.getItem('suggested-comment');

	const shouldPost = (
		(previousType === 'confirm' && currentType === 'comment') ||
		(previousType === 'confirm' && currentType === 'suggestion') ||
		(previousType === 'suggestion' && currentType === 'comment')
	);

	if (shouldPost) {
		postPreviousLogFetch(url, previousType, inputComment, suggestedComment);
	}
}

function createUrl() {
	let url = '';
	if (document.getElementById('resource-id')) {
		const resourceId = document.getElementById('resource-id').value;
		url = '/resource_comment/' + resourceId + '/comment/create_previous_log';
	}
	else if (document.getElementById('utilization-id')) {
		const utilizationId = document.getElementById('utilization-id').value;
		url = '/utilization/' + utilizationId + '/comment/create_previous_log';
	}
	return url;
}

function postPreviousLogFetch(url, previousType, inputComment, suggestedComment) {
  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      'previous_type': previousType,
      'input_comment': inputComment,
      'suggested_comment': suggestedComment,
    })
  });
  return;
}

function updateSessionStorage() {
	const currentType = document.getElementById('current-type').value;

	sessionStorage.setItem('current-type', currentType);
	
	if (currentType === 'comment') {
		sessionStorage.removeItem('input-comment');
		sessionStorage.removeItem('suggested-comment');
	}
	else if (currentType === 'suggestion') {
		const inputComment = document.getElementById('input-comment').value;
		let suggestedComment = 'AUTO_SUGGEST_FAILED';
		if (document.getElementById('suggested-comment')) {
			suggestedComment = document.getElementById('suggested-comment').value;
		}

		sessionStorage.setItem('input-comment', inputComment);
		sessionStorage.setItem('suggested-comment', suggestedComment);
	}
	else if (currentType === 'confirm') {
		const inputComment = document.getElementById('input-comment').value;
		sessionStorage.setItem('input-comment', inputComment);
	}
}
