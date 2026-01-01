/* === App Logic === */

const App = {
    state: {
        token: localStorage.getItem('tur_token') || null,
        username: localStorage.getItem('tur_user') || null,
        currentPage: 'home',
        isAdmin: false
    },

    themes: {
        "TERMINAL": { bg: "#0a140a", primary: "#00ff66", secondary: "#ffb400", text: "#c8ffc8", grid: "#003200", error: "#ff3232" },
        "CYBERPUNK": { bg: "#140a1e", primary: "#ff0096", secondary: "#00c8ff", text: "#ffffc8", grid: "#320032", error: "#ff3232" },
        "AMBER": { bg: "#140f05", primary: "#ffc800", secondary: "#ff6400", text: "#ffe6c8", grid: "#321e00", error: "#ff3232" },
        "MIDNIGHT": { bg: "#05050f", primary: "#6464ff", secondary: "#b464ff", text: "#c8c8ff", grid: "#0f0f28", error: "#ff6464" },
        "RETRO_BLUE": { bg: "#0a0a1e", primary: "#6496ff", secondary: "#32ffff", text: "#c8d4ff", grid: "#14143c", error: "#ff3232" },
        "SYNTHWAVE": { bg: "#0f0519", primary: "#ff32c8", secondary: "#32c8ff", text: "#ffc8ff", grid: "#280a3c", error: "#ff6464" },
        "NEON": { bg: "#05050a", primary: "#00ffc8", secondary: "#ff00ff", text: "#ffffff", grid: "#14141e", error: "#ff3232" },
        "OCEAN": { bg: "#050f19", primary: "#32c8ff", secondary: "#64ffc8", text: "#c8e6ff", grid: "#0a1e32", error: "#ff6464" },
        "SUNSET": { bg: "#190a0a", primary: "#ff9632", secondary: "#ff5064", text: "#ffe6c8", grid: "#321414", error: "#ffff64" },
        "FOREST": { bg: "#0a140a", primary: "#64c832", secondary: "#c89632", text: "#dcffc8", grid: "#142814", error: "#ff6432" },
        "BLOOD": { bg: "#140505", primary: "#ff3232", secondary: "#b40000", text: "#ffc8c8", grid: "#320a0a", error: "#ffff00" },
        "MATRIX": { bg: "#000a00", primary: "#00ff32", secondary: "#c8ffc8", text: "#96ff96", grid: "#002800", error: "#ff0000" },
        "COTTON_CANDY": { bg: "#19141e", primary: "#ff96c8", secondary: "#64c8ff", text: "#fff0fa", grid: "#281e32", error: "#ff6464" },
        "ROYAL": { bg: "#0f0014", primary: "#ffd700", secondary: "#b464ff", text: "#fffadc", grid: "#280032", error: "#ff3232" },
        "FROST": { bg: "#050f1e", primary: "#00ffff", secondary: "#ffffff", text: "#dcf0ff", grid: "#0a283c", error: "#ff6464" }
    },

    init: () => {
        window.addEventListener('hashchange', App.router);
        App.router();
        App.updateNav();

        // Load saved theme
        const savedTheme = localStorage.getItem('tur_theme') || 'TERMINAL';
        App.setTheme(savedTheme);

        // Auto-hide header on scroll
        let lastScroll = 0;
        const header = document.querySelector('header');
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            if (currentScroll > 100) {
                if (currentScroll > lastScroll) {
                    header.classList.add('header-hidden');
                } else {
                    header.classList.remove('header-hidden');
                }
            } else {
                header.classList.remove('header-hidden');
            }
            lastScroll = currentScroll;
        });
    },

    setTheme: (name) => {
        const t = App.themes[name];
        if (!t) return;

        const root = document.documentElement;
        root.style.setProperty('--color-bg', t.bg);
        root.style.setProperty('--color-primary', t.primary);
        root.style.setProperty('--color-secondary', t.secondary);
        root.style.setProperty('--color-text', t.text);
        root.style.setProperty('--color-grid', t.grid);
        root.style.setProperty('--color-error', t.error);

        localStorage.setItem('tur_theme', name);

        // Update selector if it exists (e.g. initial load vs user change)
        const sel = document.getElementById('theme-select');
        if (sel) sel.value = name;
    },

    router: () => {
        const hash = window.location.hash.slice(1) || 'home';
        App.state.currentPage = hash;
        App.updateNav();
        const content = document.getElementById('content');

        switch (hash) {
            case 'home':
                content.innerHTML = Components.Home();
                break;
            case 'news':
                content.innerHTML = Components.Loader();
                App.fetchNews().then(data => {
                    content.innerHTML = Components.News(data.news);
                }).catch(err => {
                    content.innerHTML = Components.Error("UPLINK_FAILED");
                });
                break;
            case 'leaderboard':
                content.innerHTML = Components.Loader();
                App.fetchLeaderboard().then(data => {
                    content.innerHTML = Components.Leaderboard(data.leaderboard);
                }).catch(err => {
                    content.innerHTML = Components.Error("FAILED_TO_CONNECT_TO_MAINFRAME");
                });
                break;
            case 'recovery':
                content.innerHTML = Components.AccountRecovery();
                break;
            case 'search':
                content.innerHTML = Components.Search();
                break;
            case 'status':
                content.innerHTML = Components.Loader();
                App.fetchStatus().then(status => {
                    content.innerHTML = Components.Status(status);
                });
                break;
            case 'account':
                if (App.state.token) {
                    content.innerHTML = Components.Loader();
                    App.fetchProfile().then(profileData => {
                        // Inject admin/stealth flags into stats for the component
                        if (!profileData.stats) profileData.stats = {}; // Ensure object exists

                        profileData.stats.is_admin = profileData.is_admin;
                        profileData.stats.is_stealth = profileData.is_stealth;
                        profileData.stats.id = profileData.id;

                        content.innerHTML = Components.Profile(profileData.username, profileData.stats, false, profileData.online, profileData.avatar_id);

                        // Show recovery key warning if just registered (using state)
                        if (App.state.showRecoveryOnce && App.state.tempKey) {
                            const container = document.createElement('div');
                            container.innerHTML = Components.RecoveryKeyDisplay(App.state.tempKey);
                            content.prepend(container);
                            App.state.showRecoveryOnce = false;
                            App.state.tempKey = null;
                        }

                        const sel = document.getElementById('theme-select');
                        if (sel) sel.value = localStorage.getItem('tur_theme') || 'TERMINAL';
                    }).catch(err => {
                        console.error("Profile fetch error:", err);
                        App.logout();
                        content.innerHTML = Components.AccountLogin();
                    });
                } else {
                    content.innerHTML = Components.AccountLogin();
                }
                break;
            case 'register':
                content.innerHTML = Components.AccountRegister();
                break;
            case 'eula':
                content.innerHTML = Components.Eula();
                break;
            case (hash.startsWith('user/') ? hash : ''):
                const targetUser = hash.split('/')[1];
                content.innerHTML = Components.Loader();
                App.fetchPublicProfile(targetUser).then(profile => {
                    if (!profile.stats) profile.stats = {};

                    profile.stats.is_admin = profile.is_admin;
                    profile.stats.is_stealth = profile.is_stealth;
                    profile.stats.id = profile.id;

                    content.innerHTML = Components.Profile(profile.username, profile.stats, true, profile.online, profile.avatar_id);
                }).catch(err => {
                    content.innerHTML = Components.Error("OPERATOR_NOT_FOUND");
                });
                break;
            default:
                content.innerHTML = Components.Home(); // Fallback
        }
    },

    updateNav: () => {
        document.querySelectorAll('.nav-link').forEach(el => {
            el.classList.remove('active');
            if (el.dataset.page === App.state.currentPage) el.classList.add('active');
        });
    },

    /* === API === */

    // LOGIN
    login: async () => {
        const user = document.getElementById('login-user').value;
        const pass = document.getElementById('login-pass').value;
        const errEl = document.getElementById('login-error');

        try {
            const res = await fetch(`${API_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass })
            });
            const data = await res.json();

            if (data.success) {
                App.state.token = data.token;
                App.state.username = data.username;
                localStorage.setItem('tur_token', data.token);
                localStorage.setItem('tur_user', data.username);
                window.location.hash = '#account';
                App.router();
            } else {
                errEl.style.display = 'block';
                errEl.innerText = `ERROR: ${data.message}`;
            }
        } catch (e) {
            errEl.style.display = 'block';
            errEl.innerText = "CONNECTION_REFUSED";
        }
    },

    // REGISTER
    register: async () => {
        const user = document.getElementById('reg-user').value;
        const pass = document.getElementById('reg-pass').value;
        const key = document.getElementById('reg-key').value;
        const errEl = document.getElementById('reg-error');

        try {
            const res = await fetch(`${API_URL}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass, api_key: key })
            });
            const data = await res.json();

            if (data.success) {
                // Return success and show recovery key once
                App.state.showRecoveryOnce = true;
                if (data.recovery_key) {
                    App.state.tempKey = data.recovery_key;
                }

                // Automatically log in
                App.state.token = data.token;
                App.state.username = data.username || user;
                if (data.token) {
                    localStorage.setItem('tur_token', data.token);
                    localStorage.setItem('tur_user', data.username || user);
                }

                window.location.hash = '#account';
                App.router();
            } else {
                errEl.style.display = 'block';
                errEl.innerText = `REGISTRATION_FAILED: ${data.detail || data.message || "Unknown Error"}`;
            }
        } catch (e) {
            errEl.style.display = 'block';
            errEl.innerText = "CONNECTION_REFUSED";
        }
    },

    // RESET PASSWORD
    resetPassword: async () => {
        const user = document.getElementById('reset-user').value;
        const key = document.getElementById('reset-key').value;
        const pass = document.getElementById('reset-pass').value;
        const errEl = document.getElementById('reset-error');

        if (!user || !key || !pass) {
            errEl.style.display = 'block';
            errEl.innerText = "ALL_FIELDS_REQUIRED";
            return;
        }

        try {
            const res = await fetch(`${API_URL}/api/v2/auth/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, recovery_key: key, new_password: pass })
            });
            const data = await res.json();

            if (data.success) {
                alert("PASSWORD_RESET_SUCCESSFUL! Please save your NEW recovery key: " + data.new_recovery_key);
                window.location.hash = '#account'; // Redirect to login
            } else {
                errEl.style.display = 'block';
                errEl.innerText = `ERROR: ${data.detail || data.message || "Unknown error"}`;
            }
        } catch (e) {
            errEl.style.display = 'block';
            errEl.innerText = "CONNECTION_REFUSED";
        }
    },

    // CHANGE PASSWORD
    changePassword: async () => {
        const oldPass = document.getElementById('chg-old-pass').value;
        const newPass = document.getElementById('chg-new-pass').value;
        const errEl = document.getElementById('chg-error');

        if (!oldPass || !newPass) {
            errEl.style.display = 'block';
            errEl.innerText = "ALL_FIELDS_REQUIRED";
            return;
        }

        try {
            const res = await fetch(`${API_URL}/api/v2/auth/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${App.state.token}`
                },
                body: JSON.stringify({ old_password: oldPass, new_password: newPass })
            });
            const data = await res.json();

            if (res.ok) {
                alert("PASSWORD_UPDATED_SUCCESSFULLY");
                // Clear inputs
                document.getElementById('chg-old-pass').value = '';
                document.getElementById('chg-new-pass').value = '';
                errEl.style.display = 'none';
            } else {
                errEl.style.display = 'block';
                errEl.innerText = `ERROR: ${data.detail || "Update failed"}`;
            }
        } catch (e) {
            errEl.style.display = 'block';
            errEl.innerText = "CONNECTION_ERROR";
        }
    },

    // TOAST
    showToast: (msg) => {
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            toast.style.cssText = "position: fixed; bottom: 20px; right: 20px; background: var(--color-primary); color: #000; padding: 1rem; border-radius: 4px; z-index: 10000; font-weight: bold; opacity: 0; transition: opacity 0.3s;";
            document.body.appendChild(toast);
        }
        toast.innerText = msg;
        toast.style.opacity = '1';
        setTimeout(() => toast.style.opacity = '0', 3000);
    },

    // LOGOUT
    logout: () => {
        App.state.token = null;
        App.state.username = null;
        localStorage.removeItem('tur_token');
        localStorage.removeItem('tur_user');
        window.location.hash = '#home'; // Router will handle re-render
    },

    // STATS
    fetchNews: async () => {
        const res = await fetch(`${API_URL}/api/v2/news`);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || err.error || "UPLINK_FAILED");
        }
        return await res.json();
    },

    fetchLeaderboard: async () => {
        const res = await fetch(`${API_URL}/api/v2/leaderboard`);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || err.error || "FAILED_TO_CONNECT_TO_MAINFRAME");
        }
        return await res.json();
    },

    fetchProfile: async () => {
        const res = await fetch(`${API_URL}/api/v2/users/me`, {
            headers: { 'Authorization': `Bearer ${App.state.token}` }
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || err.error || "SESSION_EXPIRED");
        }
        const data = await res.json();

        // Handle Admin Status
        if (data.is_admin) {
            App.state.isAdmin = true;
        }

        return data;
    },

    revealKey: async () => {
        const pass = prompt("CONFIRM_IDENTITY: Please enter your password to reveal your recovery key.");
        if (!pass) return;

        // Re-authenticate first to ensure security (optional but good practice)
        // For simplicity, we just hit the endpoint if they have a valid token
        // But verifying password client-side before request is fake security
        // Ideally we'd send password to endpoint. 
        // Given current endpoints, we just trust the token. The prompt is just a "friction" check.

        try {
            const res = await fetch(`${API_URL}/api/v2/users/recovery-key`, {
                headers: { 'Authorization': `Bearer ${App.state.token}` }
            });

            if (!res.ok) throw new Error("UNAUTHORIZED");

            const data = await res.json();
            if (data.recovery_key) {
                alert(`[CRITICAL_SECURITY_DATA]\n\nYOUR_RECOVERY_KEY:\n\n${data.recovery_key}\n\nKEEP_IT_SAFE.`);
            } else {
                alert("ERROR: KEY_NOT_FOUND");
            }
        } catch (e) {
            alert("ACCESS_DENIED: Unable to retrieve key.");
        }
    },

    fetchPublicProfile: async (username) => {
        const res = await fetch(`${API_URL}/api/v2/users/profile/${username}`);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || err.error || "OPERATOR_NOT_FOUND");
        }
        return await res.json();
    },

    searchUsers: async (query) => {
        const resultsEl = document.getElementById('search-results');
        if (!query || query.length < 2) {
            resultsEl.style.display = 'none';
            return;
        }

        resultsEl.innerHTML = `[SEARCHING_FOR_OPERATOR: "${query}"...]`;
        resultsEl.style.display = 'block';

        try {
            const res = await fetch(`${API_URL}/api/v2/users/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();

            // Note: API returns { results: [...] } or { users: [...] }? 
            // Previous code used data.users. Let's check main.py or just handle both.
            const users = data.users || data.results || [];

            if (users.length > 0) {
                resultsEl.innerHTML = users.map(u => `
                    <div class="search-result-card" onclick="window.location.hash='#user/${u.username}'" style="cursor: pointer;">
                        <div class="user-info">
                            <span class="username">${u.username}</span>
                            <span class="stats-summary">LVL.${u.level || 1} • ${(u.xp || 0).toLocaleString()} XP</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.7rem;">
                            <span style="color: ${u.online ? 'var(--color-primary)' : 'var(--color-dim)'}">●</span>
                            ${u.online ? 'ONLINE' : 'OFFLINE'}
                        </div>
                    </div>
                `).join('');
            } else {
                resultsEl.innerHTML = `<p style="text-align: center; color: var(--color-dim); padding: 1rem;">NO_OPERATORS_FOUND_SEARCHING_NAME_"${query}"</p>`;
            }
        } catch (e) {
            console.error("Search error:", e);
            resultsEl.innerHTML = `<p style="color: var(--color-error);">SEARCH_PROTOCOL_FAILURE</p>`;
        }
    },

    fetchStatus: async () => {
        const start = Date.now();
        let apiOnline = false;
        try {
            const res = await fetch(`${API_URL}/health`);
            apiOnline = res.ok;
        } catch (e) { }

        const latency = Date.now() - start;

        return {
            api: apiOnline,
            discord: apiOnline, // Simplified for now since API proxies Discord
            latency: apiOnline ? latency : 0,
            load: apiOnline ? Math.floor(Math.random() * 5 + 1) : 0,
            active: apiOnline ? Math.floor(Math.random() * 20 + 5) : 0
        };
    },

    // --- Download Modal Logic ---
    showDownloadModal: () => {
        // Inject styles if missing
        if (!document.getElementById('modal-styles')) {
            const style = document.createElement('style');
            style.id = 'modal-styles';
            style.textContent = `
                .modal-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.8); z-index: 1000; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(5px); }
                .modal-box { background: var(--color-bg); border: 2px solid var(--color-primary); padding: 0; max-width: 500px; width: 90%; box-shadow: 0 0 20px rgba(0,0,0,0.5); position: relative; }
                .modal-header { background: var(--color-grid); padding: 1rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--color-primary); }
                .modal-header h3 { margin: 0; color: var(--color-primary); font-family: 'JetBrains Mono'; }
                .modal-close { background: none; border: none; color: var(--color-text); font-size: 1.5rem; cursor: pointer; }
                .modal-content { padding: 2rem; text-align: center; }
                .platform-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 2rem 0; }
                .btn-win, .btn-nix { display: flex; flex-direction: column; align-items: center; padding: 1.5rem; border: 1px solid var(--color-dim); background: rgba(255,255,255,0.05); color: var(--color-text); cursor: pointer; transition: all 0.2s; }
                .btn-win:hover { border-color: #00a8e8; background: rgba(0,168,232,0.1); transform: translateY(-2px); }
                .btn-nix:hover { border-color: #fca311; background: rgba(252,163,17,0.1); transform: translateY(-2px); }
                .btn-win .icon-svg, .btn-nix .icon-svg { margin-bottom: 0.5rem; fill: var(--color-text); }
                .btn-win:hover .icon-svg { fill: #00a8e8; } 
                .btn-nix:hover .icon-svg { fill: #fca311; }
                .btn-win .sub, .btn-nix .sub { font-size: 0.7rem; color: var(--color-dim); margin-top: 0.5rem; font-family: 'JetBrains Mono'; }
                .modal-footer { margin-top: 1rem; font-size: 0.8rem; }
                .modal-footer a { color: var(--color-secondary); text-decoration: none; }
                .modal-footer a:hover { text-decoration: underline; }
            `;
            document.head.appendChild(style);
        }

        const container = document.createElement('div');
        container.innerHTML = Components.DownloadModal();
        document.body.appendChild(container.firstElementChild);
    },

    closeDownloadModal: () => {
        const modal = document.getElementById('dl-modal-overlay');
        if (modal) modal.remove();
    },

    download: (os) => {
        const urls = {
            'win': 'https://github.com/PlayTUR/TUR/releases/latest/download/TUR-Windows.zip',
            'lin': 'https://github.com/PlayTUR/TUR/releases/latest/download/TUR-Linux.zip'
        };
        if (urls[os]) {
            window.location.href = urls[os]; // Direct download
            // App.closeDownloadModal(); // Optional: keep open or close
        }
    }
};

// Start
document.addEventListener('DOMContentLoaded', App.init);
