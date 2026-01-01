const API_URL = "https://turapi.wyind.dev"; // API Server

/* === UI Builders === */

const AVATARS = [
    // 0: Default
    `  .---.  
 /     \\ 
|  O O  |
 \\  ^  / 
  '---'  `,
    // 1: Hacker
    `  .---.  
 /=====\\ 
| [___] |
 \\ === / 
  '---'  `,
    // 2: Robot
    `  [o_o]  
 /|___|\\ 
| [___] |
 \\_| |_/ 
   I I   `,
    // 3: Alien
    `   \\ /   
  (o.o)  
  ( > )  
 /  ^  \\ 
   | |   `,
    // 4: Ninja
    `  .---.  
 / ~~~ \\ 
|  - -  |
 \\  =  / 
  '---'  `
];

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

    DownloadModal: () => `
        <div id="dl-modal-overlay" class="modal-overlay" onclick="App.closeDownloadModal()">
            <div class="modal-box" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>SELECT_PLATFORM</h3>
                    <button class="modal-close" onclick="App.closeDownloadModal()">×</button>
                </div>
                <div class="modal-content">
                    <p>Choose your operating system for direct download:</p>
                    <div class="platform-grid">
                        <button class="btn btn-win" onclick="App.download('win')">
                            <!-- Pixel Art Windows Logo (SVG) -->
                            <svg class="icon-svg" width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="image-rendering: pixelated;">
                                <rect x="2" y="2" width="9" height="9" fill="currentColor"/>
                                <rect x="13" y="2" width="9" height="9" fill="currentColor"/>
                                <rect x="2" y="13" width="9" height="9" fill="currentColor"/>
                                <rect x="13" y="13" width="9" height="9" fill="currentColor"/>
                            </svg>
                            <span class="sub">WINDOWS .zip (64-bit)</span>
                        </button>
                        <button class="btn btn-nix" onclick="App.download('lin')">
                            <!-- Pixel Art Linux Tux Logo (Simplified SVG) -->
                            <svg class="icon-svg" width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="image-rendering: pixelated;">
                                <rect x="7" y="2" width="10" height="3" fill="currentColor"/>
                                <rect x="6" y="5" width="2" height="4" fill="currentColor"/>
                                <rect x="16" y="5" width="2" height="4" fill="currentColor"/>
                                <rect x="8" y="5" width="8" height="11" fill="currentColor"/>
                                <rect x="4" y="9" width="4" height="4" fill="currentColor"/> <!-- L Wing -->
                                <rect x="16" y="9" width="4" height="4" fill="currentColor"/> <!-- R Wing -->
                                <rect x="5" y="16" width="6" height="3" fill="currentColor"/> <!-- L Foot -->
                                <rect x="13" y="16" width="6" height="3" fill="currentColor"/> <!-- R Foot -->
                            </svg>
                            <span class="sub">LINUX .zip (x86_64)</span>
                        </button>
                    </div>
                    <div class="modal-footer">
                        <a href="https://github.com/PlayTUR/TUR/releases/latest" target="_blank">View all releases on GitHub</a>
                    </div>
                </div>
            </div>
        </div>
    `,

    Home: () => `
        <div class="hero">
            <h1 class="glitch">THE UNNAMED RHYTHM GAME</h1>
            <p class="subtitle"><span>></span> A 4-key rhythm game with custom song support</p>
            
            <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <button id="download-btn" class="btn btn-primary" onclick="App.showDownloadModal()">DOWNLOAD NOW</button>
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
                <div class="step"><span class="step-num">1</span><span class="step-text">Download the ZIP for your OS</span></div>
                <div class="step"><span class="step-num">2</span><span class="step-text">Extract to any folder</span></div>
                <div class="step"><span class="step-num">3</span><span class="step-text">Run: TUR.exe (Win) or ./TUR (Linux)</span></div>
                <div class="step"><span class="step-num">4</span><span class="step-text">Linux: chmod +x TUR first</span></div>
                <div class="step"><span class="step-num">5</span><span class="step-text">Add audio files to /songs folder</span></div>
                <div class="step"><span class="step-num">6</span><span class="step-text">Select a song and play!</span></div>
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
                <p><strong>Charts:</strong> .tur (native), .osu / .osz (partial)</p>
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
                <p>Partial .osu and .osz file support is available. Place .osu files or .osz packs alongside the audio in /songs. Native .tur charts can be shared directly between players.</p>
            </details>
            <details>
                <summary>How does multiplayer work?</summary>
                <p>One player hosts a session from the Online menu. The server is then broadcast to the global server list where other players can join. LAN play is also supported via direct connection.</p>
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
                            <th style="text-align: center;">LEVEL</th>
                            <th style="text-align: right;">EXP</th>
                            <th style="text-align: right;">TOTAL_SCORE</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            
            <div style="margin-top: 1.5rem; text-align: center;">
                <p style="color: var(--color-dim); font-size: 0.8rem;">Looking for a specific operator? <a href="#search" style="color: var(--color-primary);">[USE_SEARCH_PROTOCOL]</a></p>
            </div>
        `;
    },
    Search: () => `
        <h2>OPERATOR_DIRECTORY</h2>
        <div class="panel" style="max-width: 600px; margin: 0 auto 2rem;">
            <p style="margin-bottom: 1rem; font-size: 0.8rem; color: var(--color-dim);"> Query the global user database for active operators. Minimum 2 characters required for initialization.</p>
            <div class="form-group" style="margin-bottom: 0;">
                <div style="display: flex; gap: 1rem;">
                    <input type="text" id="user-search-input" placeholder="Enter Operator ID..." style="flex: 1;" onkeyup="if(event.key==='Enter') App.searchUsers(this.value)">
                    <button class="btn btn-primary" onclick="App.searchUsers(document.getElementById('user-search-input').value)">[SEARCH]</button>
                </div>
            </div>
        </div>
        <div id="search-results" style="max-width: 600px; margin: 0 auto;"></div>
    `,

    AccountLogin: () => `
        <h2>ACCESS_CONTROL</h2>
        <div class="panel" style="max-width: 500px; margin: 0 auto;">
            <div class="form-group">
                <label>OPERATOR_ID (USERNAME)</label>
                <input type="text" id="login-user" placeholder="Enter Username...">
            </div>
            <div class="form-group">
                <label>PASSPHRASE</label>
                <input type="password" id="login-pass" placeholder="Enter Password..." onkeyup="if(event.key==='Enter') App.login()">
            </div>
            <div id="login-error" class="error-msg"></div>
            <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                <button class="btn" style="flex: 1;" onclick="App.login()">[AUTHENTICATE]</button>
            </div>
            
            <p style="margin-top: 1.5rem; font-size: 0.9rem;">
                NO_CREDENTIALS? <a href="#register" style="color: var(--color-primary);">[REGISTER_NEW_ID]</a><br>
                LOST_ACCESS? <a href="#recovery" style="color: var(--color-error);">[RESET_PASSPHRASE]</a>
            </p>
        </div>
    `,

    AccountRecovery: () => `
        <h2>ACCOUNT_RECOVERY_PROTOCOL</h2>
        <div class="panel" style="max-width: 500px; margin: 0 auto;">
            <p style="margin-bottom: 1.5rem; font-size: 0.8rem; color: var(--color-dim);">
                Enter your Operator ID and the unique 16-character Recovery Key provided during registration.
                <br><br>
                <span style="color: var(--color-error);">WARNING:</span> This action will invalidate all active sessions.
            </p>
            <div class="form-group">
                <label>OPERATOR_ID</label>
                <input type="text" id="reset-user" placeholder="Enter Username...">
            </div>
            <div class="form-group">
                <label>RECOVERY_KEY</label>
                <input type="text" id="reset-key" placeholder="Enter 16-char Key...">
            </div>
            <div class="form-group">
                <label>NEW_PASSPHRASE</label>
                <input type="password" id="reset-pass" placeholder="New Password (6-64 chars)...">
            </div>
            <div id="reset-error" class="error-msg"></div>
            <div style="display: flex; gap: 1rem; margin-top: 1rem;">
                <button class="btn btn-primary" style="flex: 1;" onclick="App.resetPassword()">[EXECUTE_RESET]</button>
                <button class="btn btn-secondary" style="flex: 0 0 100px;" onclick="window.location.hash='#account'">[CANCEL]</button>
            </div>
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
    AccountRecovery: () => `
        <h2>ACCOUNT_RECOVERY_PROTOCOL</h2>
        <div class="panel" style="max-width: 500px; margin: 0 auto;">
            <p style="margin-bottom: 1.5rem; font-size: 0.8rem; color: var(--color-dim);">Enter your Operator ID and unique Recovery Key to initialize a passphrase reset. Invalidation of all active sessions will follow.</p>
            <div class="form-group">
                <label>OPERATOR_ID</label>
                <input type="text" id="reset-user" placeholder="Enter Username...">
            </div>
            <div class="form-group">
                <label>RECOVERY_KEY</label>
                <input type="text" id="reset-key" placeholder="Enter 16-character Key...">
            </div>
            <div class="form-group">
                <label>NEW_PASSPHRASE</label>
                <input type="password" id="reset-pass" placeholder="6-64 Characters...">
            </div>
            <div id="reset-error" class="error-msg"></div>
            <button class="btn btn-primary" onclick="App.resetPassword()">[EXECUTE_RESET]</button>
            <button class="btn btn-secondary" style="margin-left: 0.5rem;" onclick="window.location.hash='#account'">[CANCEL]</button>
        </div>
    `,

    RecoveryKeyDisplay: (key) => `
        <div class="panel" style="border-color: var(--color-primary); margin-top: 1rem;">
            <h3 style="color: var(--color-primary);">🔐 ACCOUNT_RECOVERY_KEY_GENERATED</h3>
            <p style="font-size: 0.8rem; margin: 0.5rem 0;">This is your <strong>ONLY</strong> way to recover your account if you forget your password. Write it down or save it securely.</p>
            <div style="background: rgba(0,255,136,0.1); padding: 1rem; text-align: center; font-family: var(--font-mono); font-size: 1.5rem; letter-spacing: 2px; border: 1px dashed var(--color-primary); margin: 1rem 0;">
                ${key}
            </div>
            <button class="btn" style="width: 100%;" onclick="this.parentElement.remove()">[ACKNOWLEDGE_AND_SECURE]</button>
        </div>
    `,

    ChangePassword: () => `
        <div class="panel" style="margin-top: 1rem; border-color: var(--color-secondary);">
            <h3>SECURITY_UPDATE</h3>
            <div class="form-group">
                <label>CURRENT_PASSPHRASE</label>
                <input type="password" id="chg-old-pass" placeholder="Verify Identity...">
            </div>
            <div class="form-group">
                <label>NEW_PASSPHRASE</label>
                <input type="password" id="chg-new-pass" placeholder="New Password...">
            </div>
            <div id="chg-error" class="error-msg"></div>
            <button class="btn btn-secondary" style="width: 100%;" onclick="App.changePassword()">[UPDATE_CREDENTIALS]</button>
        </div>
    `,

    RecoveryKeyDisplay: (key) => `
        <div class="panel" style="border-color: var(--color-primary); margin-top: 2rem; animation: slideIn 0.5s ease-out;">
            <h3 style="color: var(--color-primary); text-align: center;">⚠ CRITICAL: SAVE_THIS_KEY ⚠</h3>
            <p style="text-align: center; margin-bottom: 1rem;">
                This key is the <strong>ONLY</strong> way to restore access if you forget your password.<br>
                We do not store email addresses.
            </p>
            
            <div class="key-box" onclick="navigator.clipboard.writeText('${key}'); App.showToast('COPIED_TO_CLIPBOARD')" style="
                background: rgba(0, 0, 0, 0.3);
                border: 2px dashed var(--color-primary);
                padding: 1.5rem;
                text-align: center;
                font-family: 'JetBrains Mono', monospace;
                font-size: 1.5rem;
                letter-spacing: 2px;
                cursor: pointer;
                color: var(--color-primary);
                margin-bottom: 1rem;
                transition: all 0.2s;
            " onmouseover="this.style.background='rgba(0,255,136,0.1)'" onmouseout="this.style.background='rgba(0,0,0,0.3)'">
                ${key}
                <div style="font-size: 0.7rem; color: var(--color-dim); margin-top: 0.5rem; letter-spacing: 0;">(CLICK_TO_COPY)</div>
            </div>

            <button class="btn btn-primary" style="width: 100%;" onclick="window.location.hash='#account'">[I_HAVE_SAVED_THIS_KEY_SECURELY]</button>
        </div>
    `,

    Profile: (user, stats, isPublic = false, isOnline = false, avatarId = 0) => `
        <div style="display: flex; gap: 2rem; align-items: flex-start; margin-bottom: 1rem;">
            <div class="panel" style="padding: 1rem; width: 140px; text-align: center; flex-shrink: 0; display: flex; align-items: center; justify-content: center; min-height: 120px;">
                <pre style="font-family: 'JetBrains Mono', monospace; line-height: 1.2; font-size: 0.9rem; color: var(--color-secondary); margin: 0;">${AVATARS[avatarId || 0] || AVATARS[0]}</pre>
            </div>
            
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <h2 style="margin: 0;">OPERATOR_PROFILE: ${user}</h2>
                    <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem;">
                        <span style="color: ${isOnline ? 'var(--color-primary)' : 'var(--color-error)'}">●</span>
                        ${isOnline ? 'ONLINE' : 'OFFLINE'}
                    </div>
                </div>
                
                <div style="display: flex; gap: 1rem; align-items: center; margin-bottom: 0.5rem;">
                    <div style="color: var(--color-dim); font-size: 0.9rem;">ID: #${stats?.id || "---"}</div>
                    ${(() => {
            // Check if the PROFILE USER is admin (from DB)
            const isProfileAdmin = (stats?.is_admin);
            const isGuest = !stats || !stats.id;

            if (isProfileAdmin) {
                return `<span style="color: #ffd700; border: 1px solid #ffd700; padding: 0 4px; font-size: 0.7rem; letter-spacing: 1px;">ROOT</span>`;
            } else if (isGuest) {
                return `<span style="color: #888; border: 1px solid #888; padding: 0 4px; font-size: 0.7rem; letter-spacing: 1px;">GUEST</span>`;
            } else {
                return `<span style="color: #00ff00; border: 1px solid #00ff00; padding: 0 4px; font-size: 0.7rem; letter-spacing: 1px;">USER</span>`;
            }
        })()}
                </div>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <div class="panel">
                <h3>STATISTICS</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; margin-bottom: 1rem;">
                     <div>
                        <div style="font-size: 0.8rem; color: var(--color-secondary);">GLOBAL RANK</div>
                        <div style="font-size: 1.5rem;">#${stats?.rank || "-"}</div>
                     </div>
                     <div>
                        <div style="font-size: 0.8rem; color: var(--color-secondary);">LEVEL</div>
                        <div style="font-size: 1.5rem;">${stats?.level || 1}</div>
                     </div>
                </div>
                
                <p><strong>XP:</strong> ${(stats?.xp || 0).toLocaleString()}</p>
                <p><strong>BEST SCORE:</strong> ${(stats?.best_score || 0).toLocaleString()}</p>
                <p><strong>TOTAL SCORE:</strong> ${(stats?.total_score || stats?.score || 0).toLocaleString()}</p>
                <p><strong>MISSIONS PLAYED:</strong> ${stats?.plays || 0}</p>
                <p><strong>FAVORITE DIFFICULTY:</strong> ${stats?.fav_difficulty || "NONE"}</p>
            </div>
            
            <div class="panel">
                <h3>SESSION_INFO</h3>
                <div style="margin-bottom: 1rem;">
                    <div style="font-size: 0.8rem; color: var(--color-dim);">STATUS</div>
                    <div style="color: var(--color-primary); font-weight: bold;">ONLINE</div>
                </div>
                ${!isPublic ? `
                    <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                        ${App.state.isAdmin ? `<button class="btn btn-primary" style="width: 100%;" onclick="window.location.href='sys_root_77.html'">[ACCESS_ROOT_TERMINAL]</button>` : ''}
                        <button class="btn btn-secondary" style="width: 100%;" onclick="App.revealKey()">[REVEAL_RECOVERY_KEY]</button>
                        <button class="btn btn-secondary" style="width: 100%;" onclick="App.logout()">[TERMINATE_SESSION]</button>
                    </div>
                ` : `
                    <button class="btn" style="width: 100%;" onclick="window.location.hash='#leaderboard'">[RETURN]</button>
                `}
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
                   <p>API_GATEWAY: <span style="color: ${status.api ? 'var(--color-primary)' : 'var(--color-error)'};">${status.api ? 'ONLINE' : 'OFFLINE'}</span></p>
                   <p>DATABASE_SHARD: <span style="color: ${status.api ? 'var(--color-primary)' : 'var(--color-error)'};">${status.api ? 'ONLINE' : 'OFFLINE'}</span></p>
                   <p>AUTH_MODULE: <span style="color: ${status.api ? 'var(--color-primary)' : 'var(--color-error)'};">${status.api ? 'ONLINE' : 'OFFLINE'}</span></p>
                   <p>DISCORD_UPLINK: <span style="color: ${status.discord ? 'var(--color-primary)' : 'var(--color-error)'};">${status.discord ? 'CONNECTED' : 'OFFLINE'}</span></p>
                </div>
                <div>
                    <h3>PERFORMANCE_METRICS</h3>
                    <p>LATENCY: ${status.latency || "---"}ms</p>
                    <p>SERVER_LOAD: ${status.load || "---"}%</p>
                    <p>ACTIVE_OPERATORS: ${status.active || "---"}</p>
                </div>
            </div>
            
            <div style="margin-top: 2rem; border-top: 1px solid var(--color-grid); padding-top: 1rem;">
                <h3>MAINTENANCE_LOG</h3>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
                    ${status.api
            ? `<p style="color: var(--color-primary);">[${new Date().toISOString().split('T')[0]}] NO_INCIDENTS_REPORTED. SERVICE_STABILITY_OPTIMAL.</p>`
            : `
                        <p style="color: var(--color-error); margin-bottom: 0.5rem;">[${new Date().toISOString().split('T')[0]}] CRITICAL_FAILURE: API_GATEWAY_UNREACHABLE.</p>
                        <p style="color: var(--color-dim);">DETECTION_SOURCE: WEB_PROBE_FAILED</p>
                        <p style="color: var(--color-dim);">RECOMMENDED_ACTION: CHECK_VPS_FIREWALL_AND_PORT_80</p>
                        `
        }
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 2rem;">
                <button class="btn" onclick="window.location.hash='#home'">[RETURN]</button>
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
            // Updated to use the correct repository path
            const res = await fetch("https://api.github.com/repos/PlayTUR/TUR/releases/latest");
            if (res.ok) {
                const data = await res.json();
                Utils.latestVersion = data.tag_name;

                // Find Windows asset (direct download URL)
                const windowsAsset = data.assets.find(a => a.name.toLowerCase().includes("windows") && a.name.endsWith(".zip"));
                if (windowsAsset) {
                    Utils.downloadUrl = windowsAsset.browser_download_url;
                } else {
                    // Fallback to first zip
                    const anyZip = data.assets.find(a => a.name.endsWith(".zip"));
                    Utils.downloadUrl = anyZip ? anyZip.browser_download_url : data.html_url;
                }
            } else {
                console.warn("GitHub API returned status:", res.status);
            }
        } catch (e) {
            console.error("Version fetch failed:", e);
        } finally {
            // Always update buttons, even on failure, to clear "CHECKING..."
            Utils.updateDownloadButtons();
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
