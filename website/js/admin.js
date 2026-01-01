const API_URL = "https://turapi.wyind.dev"; // API Server production

const AdminApp = {
    state: {
        token: localStorage.getItem('tur_token'),
        username: localStorage.getItem('tur_user')
    },

    init: async () => {
        // Quick local check
        if (!AdminApp.state.token) {
            window.location.href = "index.html";
            return;
        }

        // Verify with server (and check is_admin)
        try {
            const res = await fetch(`${API_URL}/api/v2/users/me`, {
                headers: { 'Authorization': `Bearer ${AdminApp.state.token}` }
            });

            if (!res.ok) throw new Error("Auth Failed");

            const data = await res.json();
            if (!data.is_admin) {
                alert("ACCESS_DENIED: INSUFFICIENT_PRIVILEGES");
                window.location.href = "index.html";
                return;
            }

            // Success
            document.getElementById('admin-user').innerText = `OPERATOR:${data.username}`;
            document.getElementById('auth-panel').classList.add('hidden');
            document.getElementById('admin-dashboard').classList.remove('hidden');

            AdminApp.loadBans();
            AdminApp.checkPing();

        } catch (e) {
            console.error(e);
            window.location.href = "index.html";
        }
    },

    logout: () => {
        window.location.href = "index.html";
    },

    checkPing: async () => {
        const start = Date.now();
        try {
            await fetch(`${API_URL}/health`); // Assuming health endpoint exists or 404 is fast
            const ms = Date.now() - start;
            document.getElementById('ping').innerText = ms;
        } catch {
            document.getElementById('ping').innerText = "ERR";
        }
    },

    promoteUser: async () => {
        const target = document.getElementById('promote-target').value;
        if (!target) return alert("INVALID_TARGET");

        if (!confirm(`CONFIRM: GRANT ROOT ACCESS TO [${target}]?`)) return;

        try {
            const res = await fetch(`${API_URL}/api/v2/admin/promote`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AdminApp.state.token}`
                },
                body: JSON.stringify({ username: target }) // admin_key not needed with token
            });

            if (res.ok) {
                alert(`SUCCESS: [${target}] IS NOW ROOT.`);
                document.getElementById('promote-target').value = "";
            } else {
                const err = await res.json();
                alert(`ERROR: ${err.detail}`);
            }
        } catch (e) {
            alert("CONNECTION_ERROR");
        }
    },

    banUser: async () => {
        const target = document.getElementById('ban-target').value;
        const reason = document.getElementById('ban-reason').value;
        const duration = document.getElementById('ban-duration').value;

        let body = {
            reason: reason,
            duration_days: parseInt(duration),
            admin_key: null // Using token auth
        };

        if (target.includes('.')) {
            body.ip = target;
        } else {
            body.username = target;
        }

        try {
            const res = await fetch(`${API_URL}/api/v2/internal/mod/r`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AdminApp.state.token}`
                },
                body: JSON.stringify(body)
            });

            if (res.ok) {
                alert("EXECUTION_CONFIRMED");
                document.getElementById('ban-target').value = "";
                AdminApp.loadBans();
            } else {
                const err = await res.json();
                alert(`ERROR: ${err.detail}`);
            }
        } catch (e) {
            alert("CONNECTION_ERROR");
        }
    },

    loadBans: async () => {
        const listEl = document.getElementById('ban-list');
        listEl.innerHTML = "<p>LOADING...</p>";

        try {
            const res = await fetch(`${API_URL}/api/v2/internal/mod/l`, {
                headers: { 'Authorization': `Bearer ${AdminApp.state.token}` }
            });

            if (res.ok) {
                const data = await res.json();
                if (data.bans.length === 0) {
                    listEl.innerHTML = "<p>NO ACTIVE BANS</p>";
                    return;
                }

                let html = `<table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>TARGET</th>
                            <th>REASON</th>
                            <th>EXPIRES</th>
                            <th>ACTION</th>
                        </tr>
                    </thead>
                    <tbody>`;

                html += data.bans.map(b => `
                    <tr>
                        <td>${b.id}</td>
                        <td>${b.username || b.ip || "ID:" + b.user_id}</td>
                        <td>${b.reason}</td>
                        <td>${b.expires ? new Date(b.expires * 1000).toLocaleDateString() : "PERMANENT"}</td>
                        <td>
                            <button class="btn btn-secondary" style="padding: 2px 5px; font-size: 0.8rem;" 
                                onclick="AdminApp.unban('${b.username || ""}', ${b.user_id || null}, '${b.ip || ""}')">
                                LIFT
                            </button>
                        </td>
                    </tr>
                `).join('');

                html += "</tbody></table>";
                listEl.innerHTML = html;
            }
        } catch (e) {
            listEl.innerHTML = "<p>FETCH_ERROR</p>";
        }
    },

    unban: async (username, uid, ip) => {
        if (!confirm("CONFIRM LIFT BAN?")) return;

        let body = { admin_key: null };
        if (username) body.username = username;
        if (uid) body.user_id = uid;
        if (ip) body.ip = ip;

        try {
            const res = await fetch(`${API_URL}/api/v2/internal/mod/u`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AdminApp.state.token}`
                },
                body: JSON.stringify(body)
            });

            if (res.ok) {
                AdminApp.loadBans();
            } else {
                alert("FAILED");
            }
        } catch {
            alert("ERROR");
        }
    }
};

document.addEventListener('DOMContentLoaded', AdminApp.init);
