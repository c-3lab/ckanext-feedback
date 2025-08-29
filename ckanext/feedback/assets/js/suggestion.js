document.addEventListener('DOMContentLoaded', () => {
	const inputComment = document.getElementById('input-comment').value;
	const suggestedComment = document.getElementById('suggested-comment').value;

	sessionStorage.setItem('is_suggestion', 'true');
	sessionStorage.setItem('input-comment', inputComment);
	sessionStorage.setItem('suggested-comment', suggestedComment);
});
