// =========================================================
// CONFIGURATION
// =========================================================

const API_URL = "http://127.0.0.1:8000";


// =========================================================
// STATE
// =========================================================

let currentResult = null;


// =========================================================
// DOM ELEMENTS
// =========================================================

const queryInput = document.getElementById("query");
const sendButton = document.getElementById("sendButton");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error");
const responseSection = document.getElementById("responseSection");
const detailsSection = document.getElementById("detailsSection");
const approvalSection = document.getElementById("approvalSection");


// =========================================================
// RUN AGENT
// =========================================================

async function runAgent() {

    const query = queryInput.value.trim();

    if (!query) {
        showError("Please enter a question.");
        return;
    }

    hideError();
    hideElement(responseSection);
    hideElement(detailsSection);
    hideElement(approvalSection);

    showElement(loading);

    sendButton.disabled = true;

    try {

        const response = await fetch(
            `${API_URL}/run`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({
                    user_query: query,
                    approved: false
                })
            }
        );


        if (!response.ok) {

            const errorText = await response.text();

            throw new Error(
                `API request failed: ${response.status} ${errorText}`
            );
        }


        const result = await response.json();

        currentResult = result;

        displayResult(result);

    } catch (error) {

        console.error("Agent error:", error);

        showError(
            "Unable to connect to the MCPPROJECT API. " +
            "Make sure FastAPI is running on port 8000. " +
            "Error: " +
            error.message
        );

    } finally {

        hideElement(loading);

        sendButton.disabled = false;
    }
}


// =========================================================
// DISPLAY RESULT
// =========================================================

function displayResult(result) {

    const answer =
        result.final_answer ||
        result.answer ||
        result.message;


    if (answer) {

        const answerElement =
            document.getElementById("answer");

        if (answerElement) {

            answerElement.textContent = answer;

        }

        showElement(responseSection);

    } else {

        const answerElement =
            document.getElementById("answer");

        if (answerElement) {

            answerElement.textContent =
                "The agent did not return a final answer.";

        }

        showElement(responseSection);
    }


    // =====================================================
    // INTENT
    // =====================================================

    const intentElement =
        document.getElementById("intent");

    if (intentElement) {

        intentElement.textContent =
            result.intent || "Not available";
    }


    // =====================================================
    // PROJECT
    // =====================================================

    const projectElement =
        document.getElementById("project");

    if (projectElement) {

        projectElement.textContent =
            result.project_name || "Not available";
    }


    // =====================================================
    // SOURCES
    // =====================================================

    const sourcesElement =
        document.getElementById("sources");

    const sources =
        result.required_sources;

    if (sourcesElement) {

        if (
            Array.isArray(sources) &&
            sources.length > 0
        ) {

            sourcesElement.textContent =
                sources
                    .map(
                        source =>
                            String(source).toUpperCase()
                    )
                    .join(" • ");

        } else {

            sourcesElement.textContent =
                "None";
        }
    }


    // =====================================================
    // RAW EVIDENCE
    // =====================================================

    const rawEvidenceElement =
        document.getElementById("rawEvidence");

    if (rawEvidenceElement) {

        const rawEvidence =
            result.raw_evidence;

        rawEvidenceElement.textContent =
            Array.isArray(rawEvidence)
                ? rawEvidence.length
                : "Not available";
    }


    // =====================================================
    // REDACTED EVIDENCE
    // =====================================================

    const redactedEvidenceElement =
        document.getElementById("redactedEvidence");

    if (redactedEvidenceElement) {

        const redactedEvidence =
            result.redacted_evidence;

        redactedEvidenceElement.textContent =
            Array.isArray(redactedEvidence)
                ? redactedEvidence.length
                : "Not available";
    }


    // =====================================================
    // CITATION VALIDATION
    // =====================================================

    const citationElement =
        document.getElementById("citation");

    if (citationElement) {

        citationElement.textContent =
            formatValidation(
                result.citation_valid
            );
    }


    // =====================================================
    // OUTPUT VALIDATION
    // =====================================================

    const outputElement =
        document.getElementById("output");

    if (outputElement) {

        outputElement.textContent =
            formatValidation(
                result.output_valid
            );
    }


    showElement(detailsSection);


    // =====================================================
    // APPROVAL
    // =====================================================

    if (
        result.requires_approval === true &&
        result.approved !== true
    ) {

        const approvalMessage =
            document.getElementById("approvalMessage");

        if (approvalMessage) {

            approvalMessage.textContent =
                result.approval_message ||
                result.answer ||
                "This action requires your approval before execution.";
        }

        showElement(approvalSection);
    }
}


// =========================================================
// APPROVE ACTION
// =========================================================

async function approveAction() {

    if (!currentResult) {

        showError(
            "No pending action found."
        );

        return;
    }


    const query =
        currentResult.user_query ||
        queryInput.value.trim();


    if (!query) {

        showError(
            "No action request found."
        );

        return;
    }


    hideError();

    hideElement(approvalSection);

    showElement(loading);


    try {

        const response = await fetch(
            `${API_URL}/run`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },

                body: JSON.stringify({
                    user_query: query,
                    approved: true
                })
            }
        );


        if (!response.ok) {

            const errorText =
                await response.text();

            throw new Error(
                `Approval request failed: ${response.status} ${errorText}`
            );
        }


        const result =
            await response.json();


        currentResult = result;


        displayResult(result);


    } catch (error) {

        console.error(
            "Approval error:",
            error
        );

        showError(
            "The approved action could not be executed. " +
            error.message
        );

    } finally {

        hideElement(loading);
    }
}


// =========================================================
// CANCEL ACTION
// =========================================================

function cancelAction() {

    hideElement(
        approvalSection
    );

    currentResult = null;
}


// =========================================================
// CLEAR
// =========================================================

function clearQuery() {

    queryInput.value = "";

    hideElement(
        responseSection
    );

    hideElement(
        detailsSection
    );

    hideElement(
        approvalSection
    );

    hideError();

    currentResult = null;
}


// =========================================================
// ERROR HANDLING
// =========================================================

function showError(message) {

    if (!errorBox) {
        return;
    }

    errorBox.textContent =
        message;

    showElement(
        errorBox
    );
}


function hideError() {

    if (!errorBox) {
        return;
    }

    hideElement(
        errorBox
    );
}


// =========================================================
// UI HELPERS
// =========================================================

function showElement(element) {

    if (!element) {
        return;
    }

    element.classList.remove(
        "hidden"
    );
}


function hideElement(element) {

    if (!element) {
        return;
    }

    element.classList.add(
        "hidden"
    );
}


// =========================================================
// VALIDATION FORMAT
// =========================================================

function formatValidation(value) {

    if (value === true) {

        return "✅ Passed";
    }


    if (value === false) {

        return "❌ Failed";
    }


    return "Not available";
}


// =========================================================
// ENTER KEY
// =========================================================

if (queryInput) {

    queryInput.addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                runAgent();
            }
        }
    );
}