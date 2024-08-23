function checkCommentExists() {
  const comment = document.getElementById('comment-content').value;
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
  return true;
}

function checkReplyExists() {
  const errorElement = document.getElementById('reply-error');
  const reply = document.getElementById('reply_content').value;

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
      star.src = '/images/rating_star.png';
    } else {
      star.src = '/images/empty_rating_star.png';
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

//文字数カウント
document.addEventListener('DOMContentLoaded', function() {
  const textarea = document.getElementById('comment-content');
  const charCount = document.getElementById('comment-count');

  textarea.addEventListener('input', function() {
    const currentLength = textarea.value.length;
    charCount.textContent = currentLength;
  });
});
