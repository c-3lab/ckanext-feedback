function getTranslatedMessage(translationKey, placeholders = {}) {
    const translationElement = document.querySelector(`[data-key="${translationKey}"]`);
    const rawMessage = translationElement?.textContent || translationKey;

    let finalMessage = rawMessage;
    for (const [placeholder, value] of Object.entries(placeholders)) {
        finalMessage = finalMessage.replace(placeholder, value);
    }

    return finalMessage;
}

function csvDownload(action) {
    const selectElement = document.getElementById("field-add_group");
    if (selectElement.value === "") {
        const message = getTranslatedMessage('Please select one organization.');
        alert(message);
        return;
    }

    const form = document.getElementById('aggregation-form');
    form.setAttribute("action", action);
    form.submit();
}