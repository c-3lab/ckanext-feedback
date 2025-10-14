/**
 * データセット検索ページにソートオプション（ダウンロード数・いいね数）を追加
 */
document.addEventListener('DOMContentLoaded', function() {
    // 設定を読み込み
    var configElement = document.getElementById('feedback-config');
    if (!configElement) {
        console.log('[Feedback] No config element found');
        return;
    }
    
    var feedbackConfig = {
        likesEnabled: configElement.dataset.likesEnabled === 'true',
        downloadsEnabled: configElement.dataset.downloadsEnabled === 'true',
        likesLabel: configElement.dataset.likesLabel || 'Likes',
        downloadsLabel: configElement.dataset.downloadsLabel || 'Downloads'
    };
    
    console.log('[Feedback] Config loaded:', feedbackConfig);
    
    /**
     * ソートセレクトボックスにカスタムオプションを追加
     */
    function addSortOptions() {
        var sortSelect = document.querySelector('select[name="sort"]');
        
        if (!sortSelect) {
            console.log('[Feedback] Sort select not found');
            return;
        }
        
        console.log('[Feedback] Adding sort options to select');
        
        // いいね数オプションを追加
        if (feedbackConfig.likesEnabled) {
            var hasLikesOption = Array.from(sortSelect.options).some(
                opt => opt.value === 'likes desc'
            );
            if (!hasLikesOption) {
                var likesOption = document.createElement('option');
                likesOption.value = 'likes desc';
                likesOption.textContent = feedbackConfig.likesLabel;
                sortSelect.appendChild(likesOption);
                console.log('[Feedback] Added likes option');
            }
        }
        
        // ダウンロード数オプションを追加
        if (feedbackConfig.downloadsEnabled) {
            var hasDownloadsOption = Array.from(sortSelect.options).some(
                opt => opt.value === 'downloads desc'
            );
            if (!hasDownloadsOption) {
                var downloadsOption = document.createElement('option');
                downloadsOption.value = 'downloads desc';
                downloadsOption.textContent = feedbackConfig.downloadsLabel;
                sortSelect.appendChild(downloadsOption);
                console.log('[Feedback] Added downloads option');
            }
        }
        
        // URLパラメータから現在のソートを復元
        var urlParams = new URLSearchParams(window.location.search);
        var currentSort = urlParams.get('sort');
        if (currentSort) {
            sortSelect.value = currentSort;
            console.log('[Feedback] Restored sort:', currentSort);
        }

        // 変更イベントリスナーを追加（重複防止）
        if (!sortSelect.dataset.feedbackListenerAdded) {
            sortSelect.addEventListener('change', function() {
                console.log('[Feedback] Sort changed to:', this.value);
                this.form.submit();
            });
            sortSelect.dataset.feedbackListenerAdded = 'true';
        }
    }
    
    // 初期実行
    addSortOptions();
    
    // 動的コンテンツのために少し遅延して再実行
    setTimeout(addSortOptions, 500);
});
