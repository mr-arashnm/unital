// front/js/api.js
const API_BASE_URL = "http://localhost:8000/api";

async function apiFetch(endpoint, options = {}) {
    const url = API_BASE_URL + endpoint;

    try {
        const token = localStorage.getItem("token");

        const res = await fetch(url, {
            headers: {
                "Content-Type": "application/json",
                ...(token ? { "Authorization": "Bearer " + token } : {}),
                ...options.headers
            },
            ...options
        });

        if (!res.ok) {
            throw new Error(`API Error: ${res.status}`);
        }

        return await res.json();
    } catch (err) {
        console.error("Fetch Error:", err);
        alert("Error fetching data from API");
        return null;
    }
}
