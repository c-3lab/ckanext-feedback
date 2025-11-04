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
    replyImageUpload.addEventListener('change', handleReplyImageChange);
  }

  function updateCharCount(textarea, charCount) {
    const currentLength = textarea.value.length;
    charCount.textContent = currentLength;
  }

  Array.from(textareas).forEach((textarea, index) => {
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

  // Ensure reactions form always submits with a valid resource_comment_id
  const reactionsForm = document.getElementById('reactions-form');
  if (reactionsForm) {
    reactionsForm.addEventListener('submit', (e) => {
      const hidden = document.getElementById('reactions-comment-id');
      if (hidden && !hidden.value) {
        // Try to recover from last set value or focused button's data attribute
        if (window.lastReactionsCommentId) {
          hidden.value = window.lastReactionsCommentId;
        }
        if (!hidden.value && reactionsForm.dataset && reactionsForm.dataset.resourceCommentId) {
          hidden.value = reactionsForm.dataset.resourceCommentId;
        }
        if (!hidden.value) {
          const active = document.activeElement;
          const dataId = active && active.getAttribute ? active.getAttribute('data-resource-comment-id') : null;
          if (dataId) hidden.value = dataId;
        }
        // If still empty, block submit to avoid server error
        if (!hidden.value) {
          e.preventDefault();
        }
      }
    });
  }
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

function handleReplyImageChange(e) {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (event) {
      createReplyPreview(event.target.result);
    };
    reader.readAsDataURL(file);
  }
}

function uploadClicked() {
  const imageUpload = document.getElementById('imageUpload');
  if (!imageUpload) return;
  imageUpload.value = '';
  imageUpload.click();
}

function replyUploadClicked() {
  const replyImageUpload = document.getElementById('replyImageUpload');
  if (!replyImageUpload) return;
  replyImageUpload.value = '';
  replyImageUpload.click();
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
    if (imageUpload) imageUpload.value = '';
    previewContainer.innerHTML = '';
    uploadBtn.style.display = 'inline-block';
  });

  wrapper.appendChild(img);
  wrapper.appendChild(closeBtn);

  previewContainer.innerHTML = '';
  previewContainer.appendChild(wrapper);
  uploadBtn.style.display = 'none';
}

function createReplyPreview(src) {
  const replyUploadBtn = document.getElementById('replyUploadBtn');
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
  Array.from(sendButtons).forEach(button => {
    button.style.pointerEvents = "none";
    button.style.background = "#333333";
    if (!bs3) {
      button.innerHTML = spinner + button.innerHTML;
    }else{
      button.innerHTML = spinner_bs3 + button.innerHTML;
    }
  });
  sessionStorage.removeItem('is_suggestion');

  return true;
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
  if (reply && reply.length>1000) {
    if (overErrorElement) {
      overErrorElement.style.display = 'block';
    }
    is_reply_exists = false;
  }

  button.style.pointerEvents = 'auto';

  if (is_reply_exists) {
    const sendButtons = document.getElementsByName('send-button');
    sendButtons.forEach(button => {
      button.style.pointerEvents = "none";
      button.style.background = "#333333";
      if (!bs3) {
        button.innerHTML = spinner + button.innerHTML;
      } else {
        button.innerHTML = spinner_bs3 + button.innerHTML;
      }
    });
  }

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
  const hidden = document.getElementById('reactions-comment-id');
  hidden.value = resourceCommentId;
  // keep last id globally for submit fallback
  try { window.lastReactionsCommentId = resourceCommentId; } catch (e) {}
  // also store on form dataset as a reliable place
  try {
    const reactionsForm = document.getElementById('reactions-form');
    if (reactionsForm && reactionsForm.dataset) {
      reactionsForm.dataset.resourceCommentId = resourceCommentId;
    }
  } catch (e) {}
  // Fallback: if empty, recover from data attribute on the triggering button
  if (!hidden.value) {
    try {
      const active = document.activeElement;
      const dataId = active && active.getAttribute ? active.getAttribute('data-resource-comment-id') : null;
      if (dataId) hidden.value = dataId;
      if (!hidden.value && window.lastReactionsCommentId) hidden.value = window.lastReactionsCommentId;
    } catch (e) {
      // no-op
    }
  }
}

function setButtonDisable(button) {
  button.style.pointerEvents = "none"
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
