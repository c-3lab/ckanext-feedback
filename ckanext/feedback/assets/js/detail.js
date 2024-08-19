function checkCommentExists() {
  const comment = document.getElementById('comment-content').value;
  const commentNoneErrorElement = document.getElementById('comment-none-error');
  const commentOverErrorElement = document.getElementById('comment-over-error');

  // Reset display settings
  commentNoneErrorElement.style.display = 'none';
  commentOverErrorElement.style.display = 'none';

  if (!comment) {
    commentNoneErrorElement.style.display = '';
    return false;
  }
  if (comment.length>50) {
    commentOverErrorElement.style.display = '';
    return false;  
  }
  return true;
}

function checkDescriptionExists() {
  errorElement = document.getElementById('description-error');
  description = document.getElementById('description').value;

  if (description) {
    errorElement.style.display = 'none';
    return true;
  } else {
    errorElement.style.display = '';
    return false;
  }
}