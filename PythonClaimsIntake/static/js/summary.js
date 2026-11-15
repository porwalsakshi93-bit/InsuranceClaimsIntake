// summary.js — Fetch and display a read-only claim summary
//
// Responsibilities:
//   - Read the claim ID from the URL query param (?id=...) or, as a
//     fallback, from the data-claim-id attribute set by Jinja2 in
//     summary.html (populated from main.py's route handler).
//   - Fetch the claim via api.js (getClaim).
//   - Render every field read-only; missing optional fields show
//     "Not Provided" (AC-16).
//   - Reveal the Print button on successful load (AC-17).
//   - Handle 404 / unknown claim IDs with a friendly message (AC-18).
//
// Client-side rendering is read-only here; the server (routers/claims.py)
// remains the source of truth for claim data.

import { getClaim } from '/static/js/api.js';

// The page is opened via /summary?id=CLM-..., so the URL query parameter is
// the primary source. The data attribute is a safe fallback populated by
// Jinja2 so the ID is available even if the query string is stripped.
const claimId =
    new URLSearchParams(window.location.search).get('id') ||
    document.body.dataset.claimId ||
    '';

// ---------------------------------------------------------------------------
// DOM helpers
// ---------------------------------------------------------------------------

/** Escape a string for safe insertion into innerHTML. */
function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = String(value);
    return div.innerHTML;
}

// Fields rendered in the summary, in display order. Optional fields are
// flagged so the renderer can substitute "Not Provided" for missing values
// (AC-16). The order groups identity, contact, and incident details.
const SUMMARY_FIELDS = [
    { key: 'claim_id', label: 'Claim ID' },
    { key: 'policy_number', label: 'Policy Number' },
    { key: 'status', label: 'Status' },
    { key: 'first_name', label: 'First Name' },
    { key: 'last_name', label: 'Last Name' },
    { key: 'phone', label: 'Phone' },
    { key: 'email', label: 'Email', optional: true },
    { key: 'incident_date', label: 'Incident Date' },
    { key: 'loss_type', label: 'Loss Type' },
    { key: 'incident_description', label: 'Incident Description' },
    { key: 'estimated_loss_amount', label: 'Estimated Loss Amount', optional: true },
    { key: 'incident_location', label: 'Incident Location', optional: true },
    { key: 'created_at', label: 'Created At' },
];

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

/** Render the claim_id prominently at the top of the summary. */
function renderClaimHeader(claim) {
    return `<h2 class="claim-id-heading">Claim ID: ${escapeHtml(claim.claim_id)}</h2>`;
}

/** Render the full field list as label/value rows. */
function renderFields(claim) {
    return SUMMARY_FIELDS.map((field) => {
        let value = claim[field.key];

        // Optional fields show "Not Provided" when absent (AC-16).
        if (field.optional && (value === null || value === undefined || value === '')) {
            value = 'Not Provided';
        } else if (value === null || value === undefined) {
            value = '';
        }

        return (
            `<div class="summary-row">` +
            `<span class="summary-label">${escapeHtml(field.label)}</span>` +
            `<span class="summary-value">${escapeHtml(value)}</span>` +
            `</div>`
        );
    }).join('');
}

/** Populate the summary container and reveal the Print button. */
function displayClaim(claim) {
    const summaryEl = document.getElementById('claim-summary');
    const errorEl = document.getElementById('claim-error');
    const printBtn = document.querySelector('.btn-print');

    errorEl.classList.add('hidden');
    errorEl.textContent = '';

    summaryEl.innerHTML = renderClaimHeader(claim) + renderFields(claim);
    summaryEl.classList.remove('hidden');

    if (printBtn) {
        printBtn.classList.remove('hidden');
    }
}

/** Show an error message and hide the summary + print button. */
function showError(message) {
    const summaryEl = document.getElementById('claim-summary');
    const errorEl = document.getElementById('claim-error');
    const printBtn = document.querySelector('.btn-print');

    summaryEl.classList.add('hidden');
    if (printBtn) {
        printBtn.classList.add('hidden');
    }

    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
}

// ---------------------------------------------------------------------------
// Load on page ready
// ---------------------------------------------------------------------------

async function loadSummary() {
    if (!claimId) {
        showError('No claim ID specified. Please search for a claim first.');
        return;
    }

    try {
        const claim = await getClaim(claimId);
        displayClaim(claim);
    } catch (err) {
        if (err && err.status === 404) {
            showError(`Claim "${claimId}" was not found.`);
        } else {
            showError(
                (err && err.error) ||
                    'An error occurred while fetching the claim.'
            );
        }
    }
}

loadSummary();
