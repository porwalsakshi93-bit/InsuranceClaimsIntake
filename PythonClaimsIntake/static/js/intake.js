// intake.js — 4-step form navigation, validation, and submission
//
// Responsibilities:
//   - Step navigation (show/hide steps, update progress indicator)
//   - Client-side validation per step (delegates to validate.js)
//   - Building the review section from form data
//   - Submitting the claim via api.js and redirecting on success
//
// Client-side validation is a UX convenience only; the server is the
// source of truth (middleware/validate.py + Pydantic models).

import {
    validatePhone,
    validateEmail,
    validateIncidentDate,
    validateLossAmount,
    validateDescription,
} from '/static/js/validate.js';
import { submitClaim } from '/static/js/api.js';

// Maps API field names to form-step numbers so we can navigate the user
// back to the relevant step when the server returns a 422 with field errors.
const FIELD_TO_STEP = {
    first_name: 1,
    last_name: 1,
    phone: 1,
    email: 1,
    policy_number: 2,
    incident_date: 3,
    loss_type: 3,
    incident_description: 3,
    estimated_loss_amount: 3,
    incident_location: 3,
};

// ---------------------------------------------------------------------------
// DOM helpers
// ---------------------------------------------------------------------------

/** Read the trimmed value of a named form field. */
function getField(name) {
    const el = document.querySelector(`[name="${name}"]`);
    return el ? el.value.trim() : '';
}

/** Gather all form fields into a plain object keyed by API field name. */
function gatherFormData() {
    return {
        first_name: getField('first_name'),
        last_name: getField('last_name'),
        phone: getField('phone'),
        email: getField('email'),
        policy_number: getField('policy_number'),
        incident_date: getField('incident_date'),
        loss_type: getField('loss_type'),
        incident_description: getField('incident_description'),
        estimated_loss_amount: getField('estimated_loss_amount'),
        incident_location: getField('incident_location'),
    };
}

/** Escape a string for safe insertion into innerHTML. */
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/** Determine which step is currently visible (defaults to 1). */
function getCurrentStep() {
    const visible = document.querySelector('.form-step:not(.hidden)');
    if (!visible) return 1;
    return parseInt(visible.id.split('-')[1], 10);
}

/** Show a single step and update the progress indicator. */
function showStep(stepNum) {
    document.querySelectorAll('.form-step').forEach((el) => {
        el.classList.add('hidden');
    });
    document.getElementById(`step-${stepNum}`).classList.remove('hidden');

    document.querySelectorAll('.step-progress .step').forEach((el) => {
        const s = parseInt(el.dataset.step, 10);
        el.classList.toggle('active', s === stepNum);
    });
}

/** Display an error message on the given step. */
function showError(stepNum, message) {
    const el = document.getElementById(`step${stepNum}-error`);
    if (el) {
        el.textContent = message;
    }
}

/** Clear the error message on the given step. */
function clearError(stepNum) {
    const el = document.getElementById(`step${stepNum}-error`);
    if (el) {
        el.textContent = '';
    }
}

// ---------------------------------------------------------------------------
// Per-step validation (UX convenience — server is source of truth)
// ---------------------------------------------------------------------------

function validateStep1() {
    if (!getField('first_name')) {
        return { valid: false, message: 'First name is required' };
    }
    if (!getField('last_name')) {
        return { valid: false, message: 'Last name is required' };
    }
    const phoneResult = validatePhone(getField('phone'));
    if (!phoneResult.valid) {
        return { valid: false, message: phoneResult.message };
    }
    const emailResult = validateEmail(getField('email'));
    if (!emailResult.valid) {
        return { valid: false, message: emailResult.message };
    }
    return { valid: true };
}

function validateStep2() {
    if (!getField('policy_number')) {
        return { valid: false, message: 'Policy number is required' };
    }
    return { valid: true };
}

function validateStep3() {
    const incidentDate = getField('incident_date');
    if (!incidentDate) {
        return { valid: false, message: 'Incident date is required' };
    }
    const dateResult = validateIncidentDate(incidentDate);
    if (!dateResult.valid) {
        return { valid: false, message: dateResult.message };
    }
    if (!getField('loss_type')) {
        return { valid: false, message: 'Loss type is required' };
    }
    const descResult = validateDescription(getField('incident_description'));
    if (!descResult.valid) {
        return { valid: false, message: descResult.message };
    }
    const lossAmount = getField('estimated_loss_amount');
    if (lossAmount) {
        const amountResult = validateLossAmount(lossAmount);
        if (!amountResult.valid) {
            return { valid: false, message: amountResult.message };
        }
    }
    return { valid: true };
}

/** Dispatch validation to the correct step validator. */
function validateStep(stepNum) {
    switch (stepNum) {
        case 1:
            return validateStep1();
        case 2:
            return validateStep2();
        case 3:
            return validateStep3();
        default:
            return { valid: true };
    }
}

// ---------------------------------------------------------------------------
// Review section
// ---------------------------------------------------------------------------

/** Populate the step-4 review area with all entered form data. */
function buildReview() {
    const data = gatherFormData();
    const reviewSection = document.getElementById('review-section');
    if (!reviewSection) return;

    // Missing optional fields show "Not Provided" (matches AC-16).
    const rows = [
        ['First Name', data.first_name],
        ['Last Name', data.last_name],
        ['Phone', data.phone],
        ['Email', data.email || 'Not Provided'],
        ['Policy Number', data.policy_number],
        ['Incident Date', data.incident_date],
        ['Loss Type', data.loss_type],
        ['Incident Description', data.incident_description],
        ['Estimated Loss Amount', data.estimated_loss_amount || 'Not Provided'],
        ['Incident Location', data.incident_location || 'Not Provided'],
    ];

    reviewSection.innerHTML = rows
        .map(
            ([label, value]) =>
                `<div class="review-row"><strong>${escapeHtml(label)}:</strong> ${escapeHtml(String(value))}</div>`
        )
        .join('');
}

// ---------------------------------------------------------------------------
// Public API (exposed on window for inline onclick handlers in intake.html)
// ---------------------------------------------------------------------------

/**
 * Navigate to a form step. Validates the current step when moving forward;
 * going backward never blocks navigation. Entering step 4 builds the review.
 */
window.goToStep = function (stepNum) {
    const currentStep = getCurrentStep();
    clearError(currentStep);

    // Validate only when moving forward
    if (stepNum > currentStep) {
        const result = validateStep(currentStep);
        if (!result.valid) {
            showError(currentStep, result.message);
            return;
        }
    }

    if (stepNum === 4) {
        buildReview();
    }

    showStep(stepNum);
};

/**
 * Gather form data, submit the claim via the API, and redirect to the
 * summary page on success. On a 422, display field errors on the
 * relevant step. On other errors, show a message on step 4.
 */
window.submitForm = async function () {
    clearError(4);

    const data = gatherFormData();

    // Build the API payload — mandatory fields first
    const payload = {
        first_name: data.first_name,
        last_name: data.last_name,
        phone: data.phone,
        policy_number: data.policy_number,
        incident_date: data.incident_date,
        loss_type: data.loss_type,
        incident_description: data.incident_description,
    };

    // Optional fields — include only when provided
    if (data.email) {
        payload.email = data.email;
    }
    if (data.estimated_loss_amount) {
        payload.estimated_loss_amount = parseFloat(data.estimated_loss_amount);
    }
    if (data.incident_location) {
        payload.incident_location = data.incident_location;
    }

    try {
        const result = await submitClaim(payload);
        // Redirect to the read-only claim summary
        window.location.href = `/summary?id=${encodeURIComponent(result.claim_id)}`;
    } catch (err) {
        // 422 responses carry a fields dict mapping field_name -> message
        if (err.fields) {
            const entries = Object.entries(err.fields);
            if (entries.length > 0) {
                const messages = entries.map(([f, m]) => `${f}: ${m}`).join('; ');
                const [firstField] = entries[0];
                const step = FIELD_TO_STEP[firstField] || 4;
                showStep(step);
                showError(step, messages);
            } else {
                showError(4, err.error || 'Validation failed');
            }
        } else {
            showError(4, err.error || 'Submission failed');
        }
    }
};
