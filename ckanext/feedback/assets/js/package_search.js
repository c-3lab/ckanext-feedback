document.addEventListener('DOMContentLoaded', function() {
    const configElement = document.getElementById('feedback-config');
    if (!configElement) {
        return;
    }
    
    const feedbackConfig = {
        likesEnabled: configElement.dataset.likesEnabled === 'true',
        downloadsEnabled: configElement.dataset.downloadsEnabled === 'true',
        likesLabel: configElement.dataset.likesLabel || 'Likes',
        downloadsLabel: configElement.dataset.downloadsLabel || 'Downloads'
    };
    
    
    function addSortOptions() {
        const sortSelect = document.querySelector('select[name="sort"]');
        
        if (!sortSelect) {
            return;
        }
        
        
        if (feedbackConfig.likesEnabled) {
            const hasLikesOption = Array.from(sortSelect.options).some(
                opt => opt.value === 'likes_total_i desc, metadata_modified desc'
            );
            if (!hasLikesOption) {
                const likesOption = document.createElement('option');
                likesOption.value = 'likes_total_i desc, metadata_modified desc';
                likesOption.textContent = feedbackConfig.likesLabel;
                sortSelect.appendChild(likesOption);
            }
        }
        
        if (feedbackConfig.downloadsEnabled) {
            const hasDownloadsOption = Array.from(sortSelect.options).some(
                opt => opt.value === 'downloads_total_i desc, metadata_modified desc'
            );
            if (!hasDownloadsOption) {
                const downloadsOption = document.createElement('option');
                downloadsOption.value = 'downloads_total_i desc, metadata_modified desc';
                downloadsOption.textContent = feedbackConfig.downloadsLabel;
                sortSelect.appendChild(downloadsOption);
            }
        }
        
        const urlParams = new URLSearchParams(window.location.search);
        const currentSort = urlParams.get('sort');
        if (currentSort) {
            sortSelect.value = currentSort;
        }

        if (!sortSelect.dataset.feedbackListenerAdded) {
            sortSelect.addEventListener('change', function() {
                this.form.submit();
            });
            sortSelect.dataset.feedbackListenerAdded = 'true';
        }
    }
    
    addSortOptions(); 
});
