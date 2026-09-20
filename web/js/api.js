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

let catalogPromise = null;
export const getCatalog = () => (catalogPromise ||= call('GET', '/api/catalog').then((c) => {
    c.byId = new Map(c.algorithms.map((a) => [a.id, a]));
    return c;
}));
export const runAlgorithm = (id, params) => call('POST', `/api/run/${id}`, { params });
export const randomParams = (id, seed) => call('POST', `/api/random/${id}`, seed == null ? {} : { seed });
export const compareFamily = (family, params) => call('POST', `/api/compare/${family}`, { params });
