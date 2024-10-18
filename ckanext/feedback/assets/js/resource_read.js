async function like_toggle() {
    let likeButton = document.getElementById('like_button');
    const likeIcon = document.getElementById('like-icon');
    let likeCount = parseInt(likeButton.textContent.trim());
    const resourceId = document.getElementById('resource-id').value;
    let likeStatus = '';

    if (likeIcon.classList.toggle('liked')) {
        likeStatus = true;
        likeCount++;
    } else {
        likeStatus = false;
        likeCount--;
    }

    likeButton.innerHTML = `
        <i id="like-icon" class="fa-solid fa-thumbs-up ${likeIcon.classList.contains('liked') ? 'liked' : ''}"></i>
        ${likeCount}
    `

    await fetch(`${resourceId}/like_toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        body: JSON.stringify({
            likeStatus: likeStatus,
        }),
    });
}
