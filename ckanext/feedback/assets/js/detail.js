const spinner = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'
const spinner_bs3 = '<span class="fa fa-spinner fa-spin" role="status" aria-hidden="true"></span>'

document.addEventListener('DOMContentLoaded', () => {
  const textareas = document.getElementsByName('comment-content');
  const charCounts = document.getElementsByName('comment-count');
  const imageUpload = document.getElementById('imageUpload');
  const replyImageUpload = document.getElementById('replyImageUpload');
  const replyTextarea = document.getElementById('reply_content');
  const replyCount = document.getElementById('reply-count');

  if (imageUpload) {
    imageUpload.addEventListener('change', handleImageChange);
  }

  if (replyImageUpload) {
    replyImageUpload.addEventListener('change', utilizationHandleReplyImageChange);
  }

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

  if (replyTextarea && replyCount) {
    replyCount.textContent = replyTextarea.value.length;
    replyTextarea.addEventListener('input', () => {
      replyCount.textContent = replyTextarea.value.length;
    });
  }
});

window.addEventListener('pageshow', (event) => {
  if (event.persisted || performance.getEntriesByType("navigation")[0]?.type === "back_forward") {
    resetFileInput();
  }

  const sendButtons = document.getElementsByName('send-button');
  Array.from(sendButtons).forEach(sendButton => {
    sendButton.style.pointerEvents = "auto";
    sendButton.style.background = "";
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

  if (oldInput) {
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
}

function checkCommentExists(button, bs3=false) {
  let comment
  if ( button.id === "comment-button" ) {
    comment = document.getElementById('comment-content').value;
  }
  if ( button.id === "suggested-comment-button" ) {
    comment = document.getElementById('suggested-comment-content').value;
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
  Array.from(sendButtons).forEach(sendButton => {
    sendButton.style.pointerEvents = "none";
    sendButton.style.background = "#333333";
    if (!bs3) {
      sendButton.innerHTML = spinner + sendButton.innerHTML;
    }else{
      sendButton.innerHTML = spinner_bs3 + sendButton.innerHTML;
    }
  });
  sessionStorage.removeItem('is_suggestion');
  
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

function setReplyFormContent(commentId) {
  const commentHeader = document.getElementById('comment-header-' + commentId);
  const replyCommentHeader = document.getElementById('reply-comment-header');
  const content = document.getElementById('comment-content-' + commentId).textContent;

  const commentHeaderClone = commentHeader.cloneNode(true);
  replyCommentHeader.innerHTML = '';
  replyCommentHeader.appendChild(commentHeaderClone);
  document.getElementById('reply-comment').innerHTML = content;
  document.getElementById('reply-comment-id').value = commentId;
  
  const replyPreviewContainer = document.getElementById('replyPreviewContainer');
  if (replyPreviewContainer) {
    replyPreviewContainer.innerHTML = '<span class="text-muted">Image preview will appear here</span>';
    replyPreviewContainer.style.display = 'none';
  }
  
  const replyImageUpload = document.getElementById('replyImageUpload');
  if (replyImageUpload) {
    replyImageUpload.value = '';
  }
}

function utilizationReplyUploadClicked() {
  const replyImageUpload = document.getElementById('replyImageUpload');
  if (!replyImageUpload) return;
  replyImageUpload.value = '';
  replyImageUpload.click();
}

function utilizationHandleReplyImageChange(e) {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (event) {
      utilizationCreateReplyPreview(event.target.result);
    };
    reader.readAsDataURL(file);
  }
}

function utilizationCreateReplyPreview(src) {
  const replyPreviewContainer = document.getElementById('replyPreviewContainer');

  const wrapper = document.createElement('div');
  wrapper.className = 'image-preview-wrapper';

  const img = document.createElement('img');
  img.className = 'image-preview';
  img.src = src;

  const closeBtn = document.createElement('button');
  closeBtn.className = 'close-button';
  closeBtn.innerHTML = '✖';

  closeBtn.addEventListener('click', () => {
    const replyImageUpload = document.getElementById('replyImageUpload');
    if (replyImageUpload) replyImageUpload.value = '';
    replyPreviewContainer.innerHTML = '<span class="text-muted">Image preview will appear here</span>';
    replyPreviewContainer.style.display = 'none';
  });

  wrapper.appendChild(img);
  wrapper.appendChild(closeBtn);

  replyPreviewContainer.innerHTML = '';
  replyPreviewContainer.appendChild(wrapper);
  replyPreviewContainer.style.display = 'flex';
}

function toggleReplies(commentId) {
  const hidden = document.getElementById(`replies-hidden-${commentId}`);
  const toggle = document.getElementById(`replies-toggle-${commentId}`);
  if (!hidden || !toggle) return;
  const isHidden = window.getComputedStyle(hidden).display === 'none';
  if (isHidden) {
    hidden.style.display = '';
    toggle.textContent = `${toggle.dataset.hideText} (${toggle.dataset.count})`;
  } else {
    hidden.style.display = 'none';
    toggle.textContent = `${toggle.dataset.showText} (${toggle.dataset.count})`;
  }
}

function checkReplyExists(button, bs3=false) {
  button.style.pointerEvents = 'none';

  const errorElement = document.getElementById('reply-error');
  const overErrorElement = document.getElementById('reply-over-error');
  const reply = document.getElementById('reply_content').value;

  errorElement.style.display = 'none';
  if (overErrorElement) {
    overErrorElement.style.display = 'none';
  }
  
  let is_reply_exists = true;

  if (!reply) {
    errorElement.style.display = 'block';
    is_reply_exists = false;
  }
  if (reply && reply.length > 1000) {
    if (overErrorElement) {
      overErrorElement.style.display = 'block';
    }
    is_reply_exists = false;
  }

  button.style.pointerEvents = 'auto';

  if (is_reply_exists) {
    const sendButtons = document.getElementsByName('send-button');
    sendButtons.forEach(btn => {
      btn.style.pointerEvents = 'none';
      btn.style.background = '#333333';
      if (!bs3) {
        btn.innerHTML = spinner + btn.innerHTML;
      } else {
        btn.innerHTML = spinner_bs3 + btn.innerHTML;
      }
    });
  }

  return is_reply_exists;
}
