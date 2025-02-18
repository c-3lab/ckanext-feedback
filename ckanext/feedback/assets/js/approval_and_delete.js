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

function getCheckedCheckboxes(name, approval) {
    return document.querySelectorAll(`input[name="${name}"]:checked[data-approval="${approval}"]`)
}

function processAction(action, isApproval) {
    const form = document.getElementById('feedbacks-form');
    form.setAttribute("action", action);

    const resourceCommentWaiting = getCheckedCheckboxes('resource-comments-checkbox', 'False');
    const resourceCommentApproved = getCheckedCheckboxes('resource-comments-checkbox', 'True');

    const utilizationWaiting = getCheckedCheckboxes('utilization-checkbox', 'False');
    const utilizationApproved = getCheckedCheckboxes('utilization-checkbox', 'True');

    const utilizationCommentWaiting = getCheckedCheckboxes('utilization-comments-checkbox', 'False');
    const utilizationCommentApproved = getCheckedCheckboxes('utilization-comments-checkbox', 'True');

    const waitingRows = resourceCommentWaiting.length + utilizationWaiting.length + utilizationCommentWaiting.length;
    const approvedRows = resourceCommentApproved.length + utilizationApproved.length + utilizationCommentApproved.length;
    const checkedRows = waitingRows + approvedRows;

    if (checkedRows === 0) {
        alert(ckan.i18n._('Please select at least one checkbox.'));
        return;
    }

    if (isApproval && waitingRows === 0) {
        alert(ckan.i18n._('Please select the checkbox whose status is Waiting.'));
        return;
    }

    const buttonId = isApproval ? 'approval-button' : 'delete-button';
    const actionButton = document.getElementById(buttonId);
    actionButton.style.pointerEvents = 'none';

    let message;

    if (isApproval) {
        [...resourceCommentApproved, ...utilizationApproved, ...utilizationCommentApproved].forEach(checkbox => {
            checkbox.checked = false;
        });
        message = ckan.i18n.translate('Is it okay to approve checked %d item(s)?').fetch(waitingRows);
    } else {
        message = ckan.i18n.translate('Completely delete checked %d item(s). This operation cannot be undone, are you sure?').fetch(checkedRows);
    }

    requestAnimationFrame(() => {
        setTimeout(() => {
            if (!confirm(message)) {
                actionButton.style.pointerEvents = '';
                return;
            }
            form.submit();
        }, 0);
    });
}

function runApproval(action) {
    processAction(action, true);
}

function runDelete(action) {
    processAction(action, false);
}

function updateSortParameter() {
    const selectElement = document.getElementById('field-order-by');

    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('sort', selectElement.value);

    window.location.href = currentUrl.toString();
}
