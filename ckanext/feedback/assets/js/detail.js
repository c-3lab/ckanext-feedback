const spinner = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'
const spinner_bs3 = '<span class="fa fa-spinner fa-spin" role="status" aria-hidden="true"></span>'

function checkCommentExists(button, bs3=false) {
  let comment
  if ( button.id === "comment-button" ) {
    comment = document.getElementById('comment-content').value;
  }
  if ( button.id === "proposal-comment-button" ) {
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
  sendButtons.forEach(sendButton => {
    sendButton.style.pointerEvents = "none";
    sendButton.style.background = "#333333";
    if (!bs3) {
      sendButton.innerHTML = spinner + sendButton.innerHTML;
    }else{
      sendButton.innerHTML = spinner_bs3 + sendButton.innerHTML;
    }
  });
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
document.addEventListener('DOMContentLoaded', () => {
  const textareas = document.getElementsByName('comment-content');
  const charCounts = document.getElementsByName('comment-count');

  function updateCharCount(textarea, charCount) {
    const currentLength = textarea.value.length;
    charCount.textContent = currentLength;
  }

  textareas.forEach(textarea, index => {
    updateCharCount(textarea, charCounts[index]);
    textarea.addEventListener('input', () => {
      const currentLength = textarea.value.length;
      charCounts[index].textContent = currentLength;
    });
  });
});

window.addEventListener('pageshow', () => {
  const sendButtons = document.getElementsByName('send-button');
  sendButtons.forEach(sendButton => {
    sendButton.style.pointerEvents = "auto";
    sendButton.style.background = "#206b82";
    sendButton.innerHTML = sendButton.innerHTML.replace(spinner, '');
    sendButton.innerHTML = sendButton.innerHTML.replace(spinner_bs3, '');
  });
});