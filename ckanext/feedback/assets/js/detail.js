const spinner = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'

function checkCommentExists(button) {
  let comment
  if ( button.id == "comment-button" ) {
    comment = document.getElementById('comment-content').value;
  }
  if ( button.id == "proposal-comment-button" ) {
    comment = document.getElementById('proposal-comment-content').value;
  }
  const commentNoneErrorElement = document.getElementById('comment-none-error');
  const commentOverErrorElement = document.getElementById('comment-over-error');

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

function checkDescriptionExists(button) {
  errorElement = document.getElementById('description-error');
  description = document.getElementById('description').value;

  if (description) {
    button.style.pointerEvents = "none"
    errorElement.style.display = 'none';
    return true;
  } else {
    errorElement.style.display = '';
    return false;
  }
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