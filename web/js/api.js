// api.js: the only place the browser talks to the server.
// Every helper returns parsed JSON and throws an Error with a readable message on failure, so callers
// only need try/catch and can show error.message directly to the user.

// One fetch wrapper for the whole app. It distinguishes three failures: the server is unreachable, the reply
// is not JSON, and the server answered with {success: false, error} (a validation problem).
async function call(method, url, body) {
    let response;
    try {
        response = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
    } catch (e) {
        throw new Error('Cannot reach the VizOS server. Is it running?');
    }
    let data = null;
    try { data = await response.json(); } catch (e) { /* not JSON */ }
    if (!response.ok || !data || data.success === false) throw new Error((data && data.error) || `Request failed (HTTP ${response.status})`);
    return data;
}

// The catalog (all algorithms + metadata) is fetched once and cached as a Promise, so every page can await it cheaply.
// `byId` is added for quick lookups by algorithm id.
let catalogPromise = null;
export const getCatalog = () => (catalogPromise ||= call('GET', '/api/catalog').then((c) => {
    c.byId = new Map(c.algorithms.map((a) => [a.id, a]));
    return c;
}));
// POST /api/run/<id>: run an algorithm on validated params and get back steps, tiles and figure data.
export const runAlgorithm = (id, params) => call('POST', `/api/run/${id}`, { params });
// POST /api/random/<id>: ask the server for a valid random input (optionally seeded).
export const randomParams = (id, seed) => call('POST', `/api/random/${id}`, seed == null ? {} : { seed });
// POST /api/compare/<family>: run every algorithm of a family on the same input.
export const compareFamily = (family, params) => call('POST', `/api/compare/${family}`, { params });
