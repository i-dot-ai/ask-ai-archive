// @ts-check

/** @type {NodeListOf<HTMLElement>} */
const aiResponses = document.querySelectorAll('.js-ai-response');
const askForm = document.getElementById("ask-a-question-form");
const loadingResponse = document.getElementById("loading-response");
const confirmSafeForm = document.getElementById("confirm-content-is-safe-form");
const askButton = document.getElementById("ask");
const confirmSafeYesButton = document.getElementById("not-sensitive");
const confirmSafeNoButton = document.getElementById("sensitive");

function changeVisibility() {
    loadingResponse?.classList.remove("govuk-!-display-none");
    askButton?.classList.add("govuk-!-display-none");
}

function changeVisibilityAtConfirmation() {
    loadingResponse?.classList.remove("govuk-!-display-none");
    confirmSafeYesButton?.classList.add("govuk-!-display-none");
    confirmSafeNoButton?.classList.add("govuk-!-display-none");
}

if (askForm) {
    askForm.addEventListener("submit", changeVisibility);
}

if (confirmSafeForm) {
    confirmSafeForm.addEventListener("submit", changeVisibilityAtConfirmation);
}


// move focus to latest AI response on page load (if a question was just asked)
if (window.localStorage.getItem("question-asked") === "true") {
    window.localStorage.removeItem("question-asked");
    window.setTimeout(() => {
        aiResponses[aiResponses.length - 1].focus();
    }, 200); // 200ms delay otherwise skip-link receives focus when using VoiceOver
}

// indicate when a question has just been asked
askForm?.addEventListener("submit", () => {
    window.localStorage.setItem("question-asked", "true");
});
confirmSafeYesButton?.addEventListener("click", () => {
    window.localStorage.setItem("question-asked", "true");
});