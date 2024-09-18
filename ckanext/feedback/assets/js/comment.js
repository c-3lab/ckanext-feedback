const spinner = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'

function checkCommentExists(button) {
  let comment
  if ( button.id == "comment-button" ) {
    comment = document.getElementById('comment-content').value;
  }
  if ( button.id == "proposal-comment-button" ) {
    comment = document.getElementById('proposal-comment-content').value;
  }

  const rating = document.getElementById('rating').value;
  const commentNoneErrorElement = document.getElementById('comment-none-error');
  const commentOverErrorElement = document.getElementById('comment-over-error');
  const ratingErrorElement = document.getElementById('rating-error');

  // Reset display settings
  commentNoneErrorElement.style.display = 'none';
  commentOverErrorElement.style.display = 'none';

  if (!comment) {
    commentNoneErrorElement.style.display = '';
    return false;
  }
  if (comment.length>1000) {
    commentOverErrorElement.style.display = '';
    return false;
  }
  const sendButtons = document.getElementsByName('send-button');
  for (let i = 0; i < sendButtons.length; i++){
    sendButtons[i].style.pointerEvents = "none";
    sendButtons[i].style.background = "#333333";
    sendButtons[i].innerHTML = spinner + sendButtons[i].innerHTML;
  }
  return true;
}

function checkReplyExists(button) {
  const errorElement = document.getElementById('reply-error');
  const reply = document.getElementById('reply_content').value;
  button.style.pointerEvents = "none"

  if (reply) {
    errorElement.style.display = 'none';
    return true;
  } else {
    errorElement.style.display = '';
    return false;
  }
}

function selectRating(selectedStar) {
  // Set rating = to clicked star's value
  document.getElementById('rating').value = selectedStar.dataset.rating;

  const stars = document.querySelectorAll('#rateable .rating-star');

  // Loop through each star and set the appropriate star icon
  stars.forEach(star => {
    if(star.dataset.rating <= selectedStar.dataset.rating) {
      star.className = 'rating-star fa-solid fa-star';
    } else {
      star.className = 'rating-star fa-regular fa-star';
    }
  });
}

function setReplyFormContent(resourceCommentId) {
  // Set values of modal screen elements
  const category = document.getElementById('comment-category-' + resourceCommentId).textContent;
  const approved = document.getElementById('comment-created-' + resourceCommentId).textContent;
  const content = document.getElementById('comment-content-' + resourceCommentId).textContent;

  document.getElementById('selected_comment_header').innerHTML = approved + ' ' + category;
  document.getElementById('selected_comment').innerHTML = content;
  document.getElementById('selected_resource_comment_id').value = resourceCommentId;
}

function setButtonDisable(button) {
  button.style.pointerEvents = "none"
}

//文字数カウント
document.addEventListener('DOMContentLoaded', function() {
  const textareas = document.getElementsByName('comment-content');
  const charCounts = document.getElementsByName('comment-count');

  function updateCharCount(textarea, charCount) {
    const currentLength = textarea.value.length;
    charCount.textContent = currentLength;
  }

  for (let i = 0; i < textareas.length; i++){
    updateCharCount(textareas[i], charCounts[i]);
    textareas[i].addEventListener('input', function() {
      const currentLength = textareas[i].value.length;
      charCounts[i].textContent = currentLength;
    });
  }
});

window.addEventListener('pageshow', function() {
  const sendButtons = document.getElementsByName('send-button');
  for (let i = 0; i < sendButtons.length; i++){
    sendButtons[i].style.pointerEvents = "auto";
    sendButtons[i].style.background = "#206b82";
    sendButtons[i].innerHTML = sendButtons[i].innerHTML.replace(spinner, '');
  }
});
