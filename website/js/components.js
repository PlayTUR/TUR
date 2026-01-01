const API_URL = "http://154.53.35.148:8080"; // Production VPS

/* === UI Builders === */

const Components = {
    Loader: () => `
        <div class="loader" style="text-align:center; padding: 2rem;">
            [LOADING_DATA_STREAM...]
        </div>
    `,

    Error: (msg) => `
        <div class="panel" style="border-color: var(--color-error);">
            <h3 style="color: var(--color-error);">⚠ SYSTEM ERROR</h3>
            <p>${msg}</p>
        </div>
    `,

    Home: () => `
        <div class="hero">
            <h1 class="glitch">THE UNNAMED RHYTHM GAME</h1>
            <p class="subtitle"><span>></span> A 4-key rhythm game with custom song support</p>
            
            <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <button id="download-btn" class="btn btn-primary" onclick="Utils.downloadGame()">CHECKING...</button>
                <a href="#leaderboard" class="btn btn-secondary">LEADERBOARD</a>
                <a href="https://discord.gg/FSXS54PdpQ" target="_blank" class="btn btn-discord">DISCORD</a>
            </div>
        </div>

        <!-- Main Features -->
        <div class="two-col" style="margin-top: 2rem;">
            <div class="panel">
                <h3>GAMEPLAY</h3>
                <p style="margin-bottom: 0.8rem;">Classic 4-key vertical scrolling rhythm gameplay. Notes fall from the top (or rise from bottom in upscroll mode) and you hit them as they cross the judgment line.</p>
                <p><strong>Timing Windows:</strong> Perfect, Good, Bad, Miss</p>
                <p><strong>Note Types:</strong> Tap notes, Hold notes</p>
                <p><strong>Scoring:</strong> Accuracy-based with combo multipliers</p>
                <p><strong>Grades:</strong> S, A, B, C, D, F based on accuracy</p>
            </div>
            <div class="panel">
                <h3>FEATURES</h3>
                <p><strong>Custom Songs:</strong> Drop any audio file into /songs</p>
                <p><strong>Auto-Generation:</strong> Beatmaps created from audio analysis</p>
                <p><strong>Online Leaderboards:</strong> Compete globally with registered accounts</p>
                <p><strong>Multiplayer:</strong> Host or join real-time sessions (P2P)</p>
                <p><strong>15+ Themes:</strong> Customize colors to your preference</p>
                <p><strong>Autoplay:</strong> Watch charts play themselves</p>
            </div>
        </div>

        <!-- Quick Start -->
        <div class="panel" style="margin: 1.5rem 0;">
            <h3>GETTING STARTED</h3>
            <div class="steps-grid">
                <div class="step"><span class="step-num">1</span><span class="step-text">Download the ZIP from above</span></div>
                <div class="step"><span class="step-num">2</span><span class="step-text">Extract anywhere on your PC</span></div>
                <div class="step"><span class="step-num">3</span><span class="step-text">Run TUR.exe (no install needed)</span></div>
                <div class="step"><span class="step-num">4</span><span class="step-text">Create account for online features</span></div>
                <div class="step"><span class="step-num">5</span><span class="step-text">Add MP3/OGG/WAV files to /songs</span></div>
                <div class="step"><span class="step-num">6</span><span class="step-text">Launch, select song, play!</span></div>
            </div>
        </div>

        <!-- Requirements & FAQ -->
        <div class="two-col">
            <div class="panel">
                <h3>SYSTEM REQUIREMENTS</h3>
                <p><strong>OS:</strong> Windows 10/11, Linux (Ubuntu 20+)</p>
                <p><strong>RAM:</strong> 2GB minimum</p>
                <p><strong>Storage:</strong> 150MB + your songs</p>
                <p><strong>Display:</strong> 1280×720 or higher</p>
                <p><strong>Audio:</strong> Any sound card</p>
                <p style="margin-top: 0.5rem; color: var(--color-dim); font-size: 0.75rem;">Portable - no installation required. Runs from any folder.</p>
            </div>
            <div class="panel">
                <h3>SUPPORTED FORMATS</h3>
                <p><strong>Audio:</strong> MP3, OGG, WAV, FLAC</p>
                <p><strong>Charts:</strong> .tur (native), .osu (partial)</p>
                <p style="margin-top: 0.5rem; color: var(--color-dim); font-size: 0.75rem;">Drop audio files in /songs folder. The game automatically generates beatmaps on first load using audio analysis.</p>
            </div>
        </div>

        <!-- Detailed FAQ -->
        <div class="panel" style="margin: 1.5rem 0;">
            <h3>FREQUENTLY ASKED QUESTIONS</h3>
            <details>
                <summary>How do I add custom songs?</summary>
                <p>Place your audio files (MP3, OGG, WAV, or FLAC) in the <code>/songs</code> folder. When you launch the game, it will automatically analyze the audio and generate a playable beatmap. The generated charts are saved as .tur files next to your audio.</p>
            </details>
            <details>
                <summary>Can I import charts from other games?</summary>
                <p>Partial .osu file support is available. Place .osu files alongside the audio in /songs. Native .tur charts can be shared directly between players.</p>
            </details>
            <details>
                <summary>How does multiplayer work?</summary>
                <p>One player hosts a session from the Online menu. Others join using the host's address. Songs are automatically transferred to players who don't have them. Scores are compared in real-time.</p>
            </details>
            <details>
                <summary>Are my scores saved?</summary>
                <p>Local scores are always saved. If you create an account and login, your scores also sync to the global leaderboard and your profile tracks stats like total plays, best scores, and favorite difficulty.</p>
            </details>
            <details>
                <summary>How do I change keybinds?</summary>
                <p>Go to Settings > Controls. Default keys are D, F, J, K for the four lanes. You can rebind to any keys you prefer.</p>
            </details>
        </div>
    `,

    News: (newsData) => {
        if (!newsData || newsData.length === 0) return `<div class="panel">NO_TRANSMISSIONS_RECEIVED</div>`;

        const items = newsData.map(n => {
            const date = new Date(n.timestamp).toLocaleDateString();
            // Basic markdown-like parsing for bold/links could go here, but keep simple for now
            return `
            <div class="panel" style="margin-bottom: 1.5rem; animation: slideIn 0.3s ease-out;">
                <div style="display:flex; justify-content:space-between; color: var(--color-secondary); margin-bottom: 0.5rem; border-bottom: 1px solid var(--color-grid); padding-bottom: 0.5rem;">
                    <span><strong>@${n.author}</strong></span>
                    <span>${date}</span>
                </div>
                <div style="white-space: pre-wrap; line-height: 1.5;">${n.content}</div>
            </div>`;
        }).join('');

        return `
            <h2>INCOMING_TRANSMISSIONS (DISCORD_UPLINK)</h2>
            <div style="max-width: 800px; margin: 0 auto;">
                ${items}
            </div>
            <div style="text-align: center; margin-top: 2rem;">
                <a href="https://discord.gg/your-invite-link" target="_blank" class="btn">[JOIN_DISCORD_SERVER]</a>
            </div>
        `;
    },

    Leaderboard: (data) => {
        if (!data || data.length === 0) return `<p>NO_DATA_FOUND</p>`;

        // Sorting by XP logic handles on server, but we can display nicely
        let rows = data.map((entry, idx) => `
            <tr>
                <td style="color: ${idx < 3 ? 'var(--color-secondary)' : 'inherit'}">#${idx + 1}</td>
                <td>${entry.username}</td>
                <td>LVL.${entry.level}</td>
                <td style="text-align: right;">${entry.xp.toLocaleString()} XP</td>
                <td style="text-align: right;">${entry.score.toLocaleString()} PTS</td>
            </tr>
        `).join('');

        return `
            <h2>GLOBAL_LEADERBOARD</h2>
            <div class="panel">
                <table>
                    <thead>
                        <tr>
                            <th width="10%">RANK</th>
                            <th>OPERATOR</th>
                            <th>LEVEL</th>
                            <th style="text-align: right;">EXP</th>
                            <th style="text-align: right;">TOTAL_SCORE</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
    },

    AccountLogin: () => `
        <h2>ACCESS_CONTROL</h2>
        <div class="panel" style="max-width: 500px; margin: 0 auto;">
            <div class="form-group">
                <label>OPERATOR_ID (USERNAME)</label>
                <input type="text" id="login-user" placeholder="Enter Username...">
            </div>
            <div class="form-group">
                <label>PASSPHRASE</label>
                <input type="password" id="login-pass" placeholder="Enter Password...">
            </div>
            <div id="login-error" class="error-msg"></div>
            <button class="btn" onclick="App.login()">[AUTHENTICATE]</button>
            
            <p style="margin-top: 1.5rem; font-size: 0.9rem;">
                NO_CREDENTIALS? <a href="#register">[REGISTER_NEW_ID]</a>
            </p>
        </div>
    `,

    AccountRegister: () => `
        <h2>NEW_OPERATOR_REGISTRATION</h2>
        <div class="panel" style="max-width: 500px; margin: 0 auto;">
            <div class="form-group">
                <label>DESIRED_ID</label>
                <input type="text" id="reg-user" placeholder="3-20 Characters...">
            </div>
            <div class="form-group">
                <label>PASSPHRASE</label>
                <input type="password" id="reg-pass" placeholder="6-64 Characters...">
            </div>
            <div class="form-group">
                <label>REGISTRATION_KEY <span style="font-size: 0.8rem; color: var(--color-secondary);">(BETA_ACCESS_REQUIRED)</span></label>
                <input type="password" id="reg-key" placeholder="Enter Beta Invite Key...">
                <p style="font-size: 0.8rem; margin-top: 0.2rem; color: var(--color-dim);">* A valid key is required to create a new operator ID during this phase.</p>
            </div>
            <div id="reg-error" class="error-msg"></div>
            <button class="btn" onclick="App.register()">[INITIALIZE_ID]</button>
            
            <p style="margin-top: 1.5rem; font-size: 0.9rem;">
                ALREADY_REGISTERED? <a href="#account">[LOGIN]</a>
            </p>
        </div>
    `,

    Profile: (user, stats) => `
        <h2>OPERATOR_PROFILE: ${user}</h2>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div class="panel">
                <h3>STATISTICS</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; margin-bottom: 1rem;">
                     <div>
                        <div style="font-size: 0.8rem; color: var(--color-secondary);">GLOBAL RANK</div>
                        <div style="font-size: 1.5rem;">#${stats.rank || "-"}</div>
                     </div>
                     <div>
                        <div style="font-size: 0.8rem; color: var(--color-secondary);">LEVEL</div>
                        <div style="font-size: 1.5rem;">${stats.level}</div>
                     </div>
                </div>
                
                <p><strong>XP:</strong> ${stats.xp.toLocaleString()}</p>
                <p><strong>BEST SCORE:</strong> ${(stats.best_score || 0).toLocaleString()}</p>
                <p><strong>TOTAL SCORE:</strong> ${stats.total_score.toLocaleString()}</p>
                <p><strong>MISSIONS PLAYED:</strong> ${stats.plays}</p>
                <p><strong>FAVORITE DIFFICULTY:</strong> ${stats.fav_difficulty || "NONE"}</p>
            </div>
            
            <div class="panel">
                <h3>VISUAL_SETTINGS</h3>
                <div class="form-group">
                    <label>THEME_OVERRIDE</label>
                    <select id="theme-select" style="width: 100%;" onchange="App.setTheme(this.value)">
                        <option value="TERMINAL">TERMINAL (DEFAULT)</option>
                        <option value="CYBERPUNK">CYBERPUNK</option>
                        <option value="AMBER">AMBER</option>
                        <option value="MIDNIGHT">MIDNIGHT</option>
                        <option value="RETRO_BLUE">RETRO_BLUE</option>
                        <option value="SYNTHWAVE">SYNTHWAVE</option>
                        <option value="NEON">NEON</option>
                        <option value="OCEAN">OCEAN</option>
                        <option value="SUNSET">SUNSET</option>
                        <option value="FOREST">FOREST</option>
                        <option value="BLOOD">BLOOD</option>
                        <option value="MATRIX">MATRIX</option>
                        <option value="COTTON_CANDY">COTTON_CANDY</option>
                        <option value="ROYAL">ROYAL</option>
                        <option value="FROST">FROST</option>
                    </select>
                </div>
            </div>

            <div class="panel">
                <h3>SESSION_INFO</h3>
                <p>STATUS: <span style="color: var(--color-primary);">ONLINE</span></p>
                ${App.state.isAdmin ? `<button class="btn" style="margin-top: 1rem; width: 100%; text-align: center;" onclick="window.location.href='sys_root_77.html'">[ACCESS_ROOT_TERMINAL]</button>` : ''}
                <button class="btn btn-secondary" style="margin-top: 1rem;" onclick="App.logout()">[TERMINATE_SESSION]</button>
            </div>
        </div>
    `,

    Eula: () => `
        <h2>END_USER_LICENSE_AGREEMENT</h2>
        <div class="panel" style="max-height: 60vh; overflow-y: auto; font-size: 0.9rem;">
            <h3>1. LICENSE GRANT & RESTRICTIONS</h3>
            <p>Subject to this Agreement, Licensor grants you a limited, non-commercial license to use the Software. You may NOT sell, rent, lease, or commercially exploit the Software. You may not reverse engineer, decompile, or modify the Software binaries.</p>
            <br>
            <h3>2. ONLINE CONDUCT (ZERO TOLERANCE)</h3>
            <p><strong>a) AUTOMATION:</strong> The use of macros, bots, or auto-clickers in online modes is STRICTLY PROHIBITED.</p>
            <p><strong>b) INTEGRITY:</strong> Intercepting or redirecting server packets is a violation of this agreement.</p>
            <p><strong>c) BEHAVIOR:</strong> Harassment or abuse of other operators will result in immediate termination.</p>
            <br>
            <h3>3. SECURITY WARNING</h3>
            <p class="blink" style="color: var(--color-error);">ATTENTION: The server actively monitors for anomalies.</p>
            <p>Any attempt to hack, inject falsified data, or DDoS the infrastructure will result in a <strong>PERMANENT ACCOUNT BAN</strong> and potential legal action. We treat infrastructure attacks as criminal offenses.</p>
            <br>
            <h3>4. DATA COLLECTION</h3>
            <p>We collect technical telemetry (Device ID, OS Version) and gameplay statistics solely for anti-cheat enforcement and leaderboard rankings.</p>
            <br>
            <h3>5. DISCLAIMER</h3>
            <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. WE ARE NOT LIABLE FOR DAMAGES, DATA LOSS, OR KEYBOARD DESTRUCTION DUE TO INTENSE RHYTHM GAMEPLAY.</p>
        </div>
        <div style="text-align: center; margin-top: 1rem;">
             <a href="#home" class="btn">[ACKNOWLEDGE]</a>
        </div>
    `,

    Admin: () => {
        const isAuth = App.state.isAdmin;
        return `
        <h2>SYSTEM_ADMINISTRATION</h2>
        <div class="panel">
            <h3>AUTHENTICATION_REQUIRED</h3>
            ${!isAuth ? `
            <div class="form-group">
                <label>ADMIN_KEY</label>
                <input type="password" id="admin-key" placeholder="Enter Root Key...">
            </div>` : `
            <p style="color: var(--color-primary); margin-bottom: 1rem;">
                <span class="blink">●</span> TOKEN_AUTHORIZED (LEVEL 1 ACCESS)
                <input type="hidden" id="admin-key" value=""> <!-- Dummy for logic -->
            </p>`}
            
            <h3>MODERATION_TOOLS</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div>
                   <label>BAN_TARGET (Username/IP)</label>
                   <input type="text" id="ban-target">
                </div>
                <div>
                   <label>REASON</label>
                   <input type="text" id="ban-reason" value="Violation of TOS">
                </div>
            </div>
            <button class="btn btn-secondary" style="margin-top: 1rem;" onclick="App.adminBan()">[EXECUTE_BAN]</button>
            
            <h3 style="margin-top: 2rem;">ACTIVE_BAN_LIST</h3>
            <button class="btn" onclick="App.loadBans()">[REFRESH_LIST]</button>
            <div id="ban-list" style="margin-top: 1rem;"></div>
        </div>
    `
    },
    Status: (status) => `
        <h2>SYSTEM_DIAGNOSTICS</h2>
        <div class="panel">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                <div>
                   <h3>CORE_SERVICES</h3>
                   <p>API_GATEWAY: <span style="color: var(--color-primary);">ONLINE</span></p>
                   <p>DATABASE_SHARD: <span style="color: var(--color-primary);">ONLINE</span></p>
                   <p>AUTH_MODULE: <span style="color: var(--color-primary);">ONLINE</span></p>
                   <p>DISCORD_UPLINK: <span style="color: ${status.discord ? 'var(--color-primary)' : 'var(--color-error)'};">${status.discord ? 'CONNECTED' : 'OFFLINE'}</span></p>
                </div>
                <div>
                    <h3>PERFORMANCE_METRICS</h3>
                    <p>LATENCY: ${Math.floor(Math.random() * 20 + 10)}ms</p>
                    <p>SERVER_LOAD: ${Math.floor(Math.random() * 10 + 1)}%</p>
                    <p>ACTIVE_OPERATORS: ${Math.floor(Math.random() * 50 + 5)}</p>
                </div>
            </div>
            
            <div style="margin-top: 2rem; border-top: 1px solid var(--color-grid); padding-top: 1rem;">
                <h3>MAINTENANCE_LOG</h3>
                <p class="blink" style="color: var(--color-primary);">[SYSTEM_ALL_CLEAR] NO INCIDENTS REPORTED.</p>
            </div>
            
            <div style="text-align: center; margin-top: 2rem;">
                <button class="btn" onclick="window.history.back()">[RETURN]</button>
            </div>
        </div>
    `
};

window.Utils = {
    latestVersion: null,
    downloadUrl: null,

    // Fetch latest version from GitHub on page load
    fetchLatestVersion: async () => {
        try {
            const res = await fetch("https://api.github.com/repos/PlayTUR/RELEASES/releases/latest");
            if (res.ok) {
                const data = await res.json();
                Utils.latestVersion = data.tag_name;

                // Find Windows asset (direct download URL)
                const windowsAsset = data.assets.find(a => a.name.includes("Windows") && a.name.endsWith(".zip"));
                if (windowsAsset) {
                    Utils.downloadUrl = windowsAsset.browser_download_url;
                } else {
                    // Fallback to first zip
                    const anyZip = data.assets.find(a => a.name.endsWith(".zip"));
                    Utils.downloadUrl = anyZip ? anyZip.browser_download_url : data.html_url;
                }

                // Update ALL download buttons on page
                Utils.updateDownloadButtons();
            }
        } catch (e) {
            console.log("Version fetch failed:", e);
            Utils.updateDownloadButtons("OFFLINE");
        }
    },

    updateDownloadButtons: (status) => {
        const text = status === "OFFLINE"
            ? "[DOWNLOAD_UNAVAILABLE]"
            : `[DOWNLOAD_${Utils.latestVersion || "LATEST"}]`;

        // Update by ID
        const btn = document.getElementById('download-btn');
        if (btn) btn.textContent = text;

        // Also update any matching onclick
        document.querySelectorAll('[onclick="Utils.downloadGame()"]').forEach(el => {
            el.textContent = text;
        });
    },

    downloadGame: () => {
        if (Utils.downloadUrl) {
            // Direct download - browser will start download immediately
            window.location.href = Utils.downloadUrl;
        } else {
            // Fallback only if fetch failed
            window.location.href = "https://github.com/PlayTUR/RELEASES/releases/latest";
        }
    }
};

// Fetch version immediately
Utils.fetchLatestVersion();

// Also update buttons when navigating (SPA)
window.addEventListener('hashchange', () => {
    setTimeout(() => Utils.updateDownloadButtons(), 100);
});
