// api.js — Sole file making fetch() calls to the backend API
// All other JS modules import from this file. Never call fetch() elsewhere.

const API_BASE = '/api';

export async function submitClaim(claimData) {
    const resp = await fetch(`${API_BASE}/claims`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(claimData),
    });
    const data = await resp.json();
    if (!resp.ok) {
        throw { status: resp.status, ...data };
    }
    return data;
}

export async function searchClaims(query) {
    const resp = await fetch(`${API_BASE}/claims?q=${encodeURIComponent(query)}`);
    const data = await resp.json();
    if (!resp.ok) {
        throw { status: resp.status, ...data };
    }
    return data;
}

export async function getClaim(claimId) {
    const resp = await fetch(`${API_BASE}/claims/${claimId}`);
    const data = await resp.json();
    if (!resp.ok) {
        throw { status: resp.status, ...data };
    }
    return data;
}

export async function getClaimSummary(claimId) {
    const resp = await fetch(`${API_BASE}/claims/${claimId}/summary`);
    const data = await resp.json();
    if (!resp.ok) {
        throw { status: resp.status, ...data };
    }
    return data;
}

export async function getPolicy(policyNumber) {
    const resp = await fetch(`${API_BASE}/policies/${policyNumber}`);
    const data = await resp.json();
    if (!resp.ok) {
        throw { status: resp.status, ...data };
    }
    return data;
}
