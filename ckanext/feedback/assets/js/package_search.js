document.addEventListener('DOMContentLoaded', function() {
    var configElement = document.getElementById('feedback-config');
    if (!configElement) {
        return;
    }
    
    var feedbackConfig = {
        likesEnabled: configElement.dataset.likesEnabled === 'true',
        downloadsEnabled: configElement.dataset.downloadsEnabled === 'true',
        likesLabel: configElement.dataset.likesLabel || 'Likes',
        downloadsLabel: configElement.dataset.downloadsLabel || 'Downloads'
    };
    
    
    function addSortOptions() {
        var sortSelect = document.querySelector('select[name="sort"]');
        
        if (!sortSelect) {
            return;
        }
        
        
        if (feedbackConfig.likesEnabled) {
            var hasLikesOption = Array.from(sortSelect.options).some(
                opt => opt.value === 'likes desc'
            );
            if (!hasLikesOption) {
                var likesOption = document.createElement('option');
                likesOption.value = 'likes desc';
                likesOption.textContent = feedbackConfig.likesLabel;
                sortSelect.appendChild(likesOption);
            }
        }
        
        if (feedbackConfig.downloadsEnabled) {
            var hasDownloadsOption = Array.from(sortSelect.options).some(
                opt => opt.value === 'downloads desc'
            );
            if (!hasDownloadsOption) {
                var downloadsOption = document.createElement('option');
                downloadsOption.value = 'downloads desc';
                downloadsOption.textContent = feedbackConfig.downloadsLabel;
                sortSelect.appendChild(downloadsOption);
            }
        }
        
        var urlParams = new URLSearchParams(window.location.search);
        var currentSort = urlParams.get('sort');
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
