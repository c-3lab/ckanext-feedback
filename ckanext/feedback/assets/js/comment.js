const spinner = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'
const spinner_bs3 = '<span class="fa fa-spinner fa-spin" role="status" aria-hidden="true"></span>'

document.addEventListener('DOMContentLoaded', () => {
  const textareas = document.getElementsByName('comment-content');
  const charCounts = document.getElementsByName('comment-count');
  const imageUpload = document.getElementById('imageUpload');

  imageUpload.addEventListener('change', handleImageChange);

  function updateCharCount(textarea, charCount) {
    const currentLength = textarea.value.length;
    charCount.textContent = currentLength;
  }

  textareas.forEach((textarea, index) => {
    updateCharCount(textarea, charCounts[index]);
    textarea.addEventListener('input', () => {
      const currentLength = textarea.value.length;
      charCounts[index].textContent = currentLength;
    });
  });
});

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

window.addEventListener('pageshow', (event) => {
  if (event.persisted || performance.getEntriesByType("navigation")[0]?.type === "back_forward") {
    resetFileInput();
  }

  const sendButtons = document.getElementsByName('send-button');
  sendButtons.forEach(sendButton => {
    sendButton.style.pointerEvents = "auto";
    sendButton.style.background = "#206b82";
    sendButton.innerHTML = sendButton.innerHTML.replace(spinner, '');
    sendButton.innerHTML = sendButton.innerHTML.replace(spinner_bs3, '');
  });
});

function handleImageChange(e) {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (event) {
      createPreview(event.target.result);
    };
    reader.readAsDataURL(file);
  }
}

function uploadClicked() {
  const imageUpload = document.getElementById('imageUpload');
  imageUpload.value = '';
  imageUpload.click();
}

function createPreview(src) {
  const uploadBtn = document.getElementById('uploadBtn');
  const previewContainer = document.getElementById('previewContainer');

  const wrapper = document.createElement('div');
  wrapper.className = 'image-preview-wrapper';

  const img = document.createElement('img');
  img.className = 'image-preview';
  img.src = src;

  const closeBtn = document.createElement('button');
  closeBtn.className = 'close-button';
  closeBtn.innerHTML = '✖';

  closeBtn.addEventListener('click', () => {
    const imageUpload = document.getElementById('imageUpload');
    imageUpload.value = '';
    previewContainer.innerHTML = '';
    uploadBtn.style.display = 'inline-block';
  });

  wrapper.appendChild(img);
  wrapper.appendChild(closeBtn);

  previewContainer.innerHTML = '';
  previewContainer.appendChild(wrapper);
  uploadBtn.style.display = 'none';
}

function resetFileInput() {
  const oldInput = document.getElementById('imageUpload');

  const oldInputType = oldInput.type;
  const oldInputId = oldInput.id;
  const oldInputClassName = oldInput.className;
  const oldInputName = oldInput.name;
  const oldInputAccept = oldInput.accept;
  const parent = oldInput.parentNode;

  parent.removeChild(oldInput);

  const newInput = document.createElement('input');
  newInput.type = oldInputType;
  newInput.id = oldInputId;
  newInput.className = oldInputClassName;
  newInput.name = oldInputName;
  newInput.accept = oldInputAccept;

  newInput.addEventListener('change', handleImageChange);

  parent.insertBefore(newInput, parent.firstChild);
}

function checkCommentExists(button, bs3=false) {
  let comment
  if ( button.id === "comment-button" ) {
    comment = document.getElementById('comment-content').value;
  }
  if ( button.id === "suggested-comment-button" ) {
    comment = document.getElementById('suggested-comment-content').value;
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
  sendButtons.forEach(button => {
    button.style.pointerEvents = "none";
    button.style.background = "#333333";
    if (!bs3) {
      button.innerHTML = spinner + button.innerHTML;
    }else{
      button.innerHTML = spinner_bs3 + button.innerHTML;
    }
  });

  return true;
}

function checkReplyExists(button) {
  button.style.pointerEvents = 'none';

  const errorElement = document.getElementById('reply-error');
  const reply = document.getElementById('reply_content').value;

  errorElement.style.display = 'none';
  
  let is_reply_exists = true;

  if (!reply) {
    errorElement.style.display = 'block';
    is_reply_exists = false;
  }

  button.style.pointerEvents = 'auto';

  return is_reply_exists;
}

function setReplyFormContent(resourceCommentId) {
  // Set values of modal screen elements
  const commentHeader = document.getElementById('comment-header-' + resourceCommentId);
  const replyCommentHeader = document.getElementById('reply-comment-header');
  const content = document.getElementById('comment-content-' + resourceCommentId).textContent;

  const commentHeaderClone = commentHeader.cloneNode(true);
  replyCommentHeader.innerHTML = '';
  replyCommentHeader.appendChild(commentHeaderClone);
  document.getElementById('reply-comment').innerHTML = content;
  document.getElementById('reply-comment-id').value = resourceCommentId;
}

function setReactionsFormContent(resourceCommentId) {
  const commentHeader = document.getElementById('comment-header-' + resourceCommentId);
  const reactionsCommentHeader = document.getElementById('reactions-comment-header');
  const commentStatus = document.getElementById('comment-badge-' + resourceCommentId);
  const adminLikeIndicator = document.getElementById('admin-liked-' + resourceCommentId);
  const content = document.getElementById('comment-content-' + resourceCommentId).textContent;

  const commentHeaderClone = commentHeader.cloneNode(true);
  reactionsCommentHeader.innerHTML = '';
  reactionsCommentHeader.appendChild(commentHeaderClone);
  if (commentStatus) {
    document.getElementById(commentStatus.dataset.status).checked = true;
  }
  document.getElementById('admin-liked').checked = adminLikeIndicator ? true : false;
  document.getElementById('reactions-comment').innerHTML = content;
  document.getElementById('reactions-comment-id').value = resourceCommentId;
}

function setButtonDisable(button) {
  button.style.pointerEvents = "none"
}
