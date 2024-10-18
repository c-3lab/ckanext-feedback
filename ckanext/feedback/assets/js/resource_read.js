let likedCounter = document.getElementById('liked_counter');
let likeIcon = document.getElementById('like-icon');
let resourceId = document.getElementById('resource-id').value;

async function like_toggle() {
    let likeStatus = '';
    if (likeIcon.classList.toggle('liked')) {
        likeStatus = 'on';
        likedCounter.textContent = parseInt(likedCounter.textContent) + 1
    } else {
        likeStatus = 'off';
        likedCounter.textContent = parseInt(likedCounter.textContent) - 1
    }

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
