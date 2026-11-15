// validate.js — Client-side validation (UX convenience only, never trust as security)

/**
 * Each validator returns { valid: boolean, message: string }.
 * These mirror the server-side rules in middleware/validate.py but are a
 * UX convenience only — server-side validation is the source of truth.
 */

export function validatePhone(phone) {
    // Strip non-digits, check 10-15 digits
    const digits = phone.replace(/\D/g, '');
    if (digits.length < 10 || digits.length > 15) {
        return { valid: false, message: 'Phone must be 10-15 digits' };
    }
    return { valid: true, message: '' };
}

export function validateEmail(email) {
    // Empty/None is valid (optional field)
    if (!email) return { valid: true, message: '' };
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!re.test(email)) return { valid: false, message: 'Invalid email format' };
    return { valid: true, message: '' };
}

export function validateIncidentDate(dateStr) {
    if (!dateStr) return { valid: false, message: 'Date is required' };
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return { valid: false, message: 'Invalid date format' };
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (date > today) return { valid: false, message: 'Incident date cannot be in the future' };
    return { valid: true, message: '' };
}

export function validateLossAmount(amount) {
    if (!amount) return { valid: true, message: '' };  // optional
    const num = parseFloat(amount);
    if (isNaN(num) || num <= 0) return { valid: false, message: 'Estimated loss amount must be greater than 0' };
    return { valid: true, message: '' };
}

export function validateDescription(text) {
    if (!text || text.length < 10) return { valid: false, message: 'Description must be at least 10 characters' };
    if (text.length > 2000) return { valid: false, message: 'Description must not exceed 2000 characters' };
    return { valid: true, message: '' };
}
