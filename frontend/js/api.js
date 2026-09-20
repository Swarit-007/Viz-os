// POST JSON to the backend. Throws Error(message) using the server's message when present.
export async function post(url, body) {
    let response;
    try {
        response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
    } catch (e) {
        throw new Error('Cannot reach the VizOS server. Is it running?');
    }
    let data = null;
    try {
        data = await response.json();
    } catch (e) {
        /* non-JSON body */
    }
    if (!response.ok || !data || data.success === false) {
        throw new Error((data && data.error) || `Request failed (HTTP ${response.status})`);
    }
    return data;
}
