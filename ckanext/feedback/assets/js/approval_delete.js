const targetCheckboxAll = document.getElementById('target-checkbox-all');
targetCheckboxAll.addEventListener('change', changeAllCheckbox);

function changeAllCheckbox(e){
    let rows;
    rows = document.querySelectorAll('.target');

    rows.forEach(row => {
        const targetCheckbox = row.querySelector('input[type="checkbox"]');
        targetCheckbox.checked = e.target.checked;
    })
}

function runBulkAction(action) {
    const form = document.getElementById('comments-form');
    form.setAttribute("action", action);
    
    const resourceCommentWaiting = document.querySelectorAll('input[name="resource-comments-checkbox"]:checked[data-approval="False"]');
    const resourceCommentApproved = document.querySelectorAll('input[name="resource-comments-checkbox"]:checked[data-approval="True"]');
    const utilizationWaiting = document.querySelectorAll('input[name="utilization-checkbox"]:checked[data-approval="False"]');
    const utilizationApproved = document.querySelectorAll('input[name="utilization-checkbox"]:checked[data-approval="True"]');
    const utilizationCommentWaiting = document.querySelectorAll('input[name="utilization-comments-checkbox"]:checked[data-approval="False"]');
    const utilizationCommentApproved = document.querySelectorAll('input[name="utilization-comments-checkbox"]:checked[data-approval="True"]');

    const waitingRows = resourceCommentWaiting.length + utilizationWaiting.length + utilizationCommentWaiting.length;
    const approvedRows = resourceCommentApproved.length + utilizationApproved.length + utilizationCommentApproved.length;
    const checkedRows = waitingRows + approvedRows;

    if (checkedRows === 0) {
        alert(ckan.i18n._('Please select at least one checkbox.'));
        return;
    }

    let bulkButtonList = document.getElementsByClassName('bulk-button');

    let message;
    if (action.includes('approve')) {
        bulkButtonList[0].style.pointerEvents = 'none';
        resourceCommentApproved.forEach(checkbox => checkbox.checked = false);
        utilizationApproved.forEach(checkbox => checkbox.checked = false);
        utilizationCommentApproved.forEach(checkbox => checkbox.checked = false);
        
        if (waitingRows === 0) {
            alert(ckan.i18n._('Please select the checkbox whose status is Waiting.'));
            return;
        }
        message = ckan.i18n.translate('Is it okay to approve checked %d item(s)?').fetch(waitingRows);
    } else  {
        bulkButtonList[1].style.pointerEvents = 'none';
        message = ckan.i18n.translate('Is it okay to delete checked %d item(s)?').fetch(checkedRows);
    }

    requestAnimationFrame(() => {
        setTimeout(() => {
            if (!confirm(message)) {
                bulkButtonList[0].style.pointerEvents = '';
                bulkButtonList[1].style.pointerEvents = '';
                return;
            }
            form.submit();
        }, 0);
    });
}

function updateSortParameter() {
    const selectElement = document.getElementById('field-order-by');

    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('sort', selectElement.value);

    window.location.href = currentUrl.toString();
}
