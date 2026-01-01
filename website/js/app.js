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
            case 'status':
                content.innerHTML = Components.Loader();
                App.fetchStatus().then(status => {
                    content.innerHTML = Components.Status(status);
                });
                break;
            case 'account':
                if (App.state.token) {
                    content.innerHTML = Components.Loader();
                    App.fetchProfile().then(stats => {
                        content.innerHTML = Components.Profile(App.state.username, stats);
                        // Ensure selector matches current state after render
                        const sel = document.getElementById('theme-select');
                        if (sel) sel.value = localStorage.getItem('tur_theme') || 'TERMINAL';
                    }).catch(err => {
                        // Token invalid?
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
                App.state.token = data.token;
                App.state.username = data.username;
                localStorage.setItem('tur_token', data.token);
                localStorage.setItem('tur_user', data.username);
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
        if (!res.ok) throw new Error("Failed");
        return await res.json();
    },

    fetchLeaderboard: async () => {
        const res = await fetch(`${API_URL}/api/v2/leaderboard`);
        if (!res.ok) throw new Error("Failed");
        return await res.json();
    },

    fetchProfile: async () => {
        const res = await fetch(`${API_URL}/api/v2/users/me`, {
            headers: { 'Authorization': `Bearer ${App.state.token}` }
        });
        if (!res.ok) throw new Error("Failed");
        const data = await res.json();

        // Handle Admin Status
        if (data.is_admin) {
            App.state.isAdmin = true;
        }

        return data.stats; // Return just stats for profile render
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
    }
};

// Start
document.addEventListener('DOMContentLoaded', App.init);
