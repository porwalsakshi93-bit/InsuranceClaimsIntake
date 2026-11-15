// search.js — Search claims by ID or last name
// Uses api.js (sole fetch file) for all API calls.

import { searchClaims } from '/static/js/api.js';

// Expose performSearch on window for the onclick handler in search.html
window.performSearch = async function () {
    const query = document.getElementById('search-query').value.trim();
    if (!query) return;

    const resultsDiv = document.getElementById('search-results');

    try {
        const results = await searchClaims(query);
        renderResults(results);
    } catch (err) {
        resultsDiv.innerHTML = `<p class="error-msg">${escapeHtml(err.error || 'Search failed')}</p>`;
    }
};

function renderResults(results) {
    const resultsDiv = document.getElementById('search-results');

    if (!results || results.length === 0) {
        resultsDiv.innerHTML = '<p>No results found.</p>';
        return;
    }

    const rows = results.map(r => `
        <tr>
            <td><a href="/summary?id=${encodeURIComponent(r.claim_id)}">${escapeHtml(r.claim_id)}</a></td>
            <td>${escapeHtml(r.first_name)} ${escapeHtml(r.last_name)}</td>
            <td>${escapeHtml(r.policy_number)}</td>
            <td>${escapeHtml(r.loss_type)}</td>
            <td>${escapeHtml(r.incident_date)}</td>
            <td>${escapeHtml(r.status)}</td>
        </tr>
    `).join('');

    resultsDiv.innerHTML = `
        <table class="results-table">
            <thead>
                <tr>
                    <th>Claim ID</th>
                    <th>Name</th>
                    <th>Policy Number</th>
                    <th>Loss Type</th>
                    <th>Incident Date</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = String(str ?? '');
    return div.innerHTML;
}

// Allow Enter key in search input to trigger search
document.getElementById('search-query').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        window.performSearch();
    }
});
