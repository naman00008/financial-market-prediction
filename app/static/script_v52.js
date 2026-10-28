// Route API requests to live EC2 backend if hosted on AWS S3 or running standalone locally
(function() {
    const isRemoteBackend = window.location.hostname.includes("s3-website") || 
                            (window.location.hostname.includes("amazonaws.com") && window.location.hostname.includes("s3")) ||
                            window.location.protocol === "file:" ||
                            window.location.hostname === "localhost" ||
                            window.location.hostname === "127.0.0.1";
    if (isRemoteBackend) {
        const originalFetch = window.fetch;
        const EC2_BACKEND = "http://13.217.227.166";
        window.fetch = function(url, options) {
            if (typeof url === 'string' && url.startsWith('/api/')) {
                url = EC2_BACKEND + url;
            }
            return originalFetch(url, options);
        };
    }
})();

document.addEventListener("DOMContentLoaded", () => {
    // ==========================================
    // --- Authentication & Session Management ---
    // ==========================================
    const AUTH_STORAGE_KEY = "market_ml_user";
    const AUTH_TOKEN_KEY = "market_ml_token";

    const PUBLIC_TABS = ["analysis"];
    const TAB_NAMES = {
        "analysis": "Market Analysis",
        "evaluation": "AI Model Evaluation",
        "backtest": "Strategy Backtest",
        "forecast": "1-Year Monte Carlo Forecast",
        "portfolio": "Portfolio Optimization & Risk Engine",
        "news": "News & Financial Sentiment"
    };

    let pendingTargetTabId = null;

    function getStoredUser() {
        try {
            const raw = localStorage.getItem(AUTH_STORAGE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    function getStoredToken() {
        return localStorage.getItem(AUTH_TOKEN_KEY) || "";
    }

    function isUserAuthenticated() {
        return !!getStoredUser();
    }

    function setStoredSession(user, token) {
        if (user) {
            localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
        }
        if (token) {
            localStorage.setItem(AUTH_TOKEN_KEY, token);
        }
        renderAuthUI();
    }

    function clearStoredSession() {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        localStorage.removeItem(AUTH_TOKEN_KEY);
        renderAuthUI();
    }

    const authSignInBtn = document.getElementById("auth-signin-btn");
    const authUserBadge = document.getElementById("auth-user-badge");
    const authUserName = document.getElementById("auth-user-name");
    const authUserAvatar = document.getElementById("auth-user-avatar");
    const authUserTier = document.getElementById("auth-user-tier");
    const authLogoutBtn = document.getElementById("auth-logout-btn");

    const authModal = document.getElementById("auth-modal");
    const authModalClose = document.getElementById("auth-modal-close");
    const authGateBanner = document.getElementById("auth-gate-banner");
    const authGateMessage = document.getElementById("auth-gate-message");
    const authAlert = document.getElementById("auth-alert");

    const tabBtnLogin = document.getElementById("tab-btn-login");
    const tabBtnSignup = document.getElementById("tab-btn-signup");
    const authLoginForm = document.getElementById("auth-login-form");
    const authSignupForm = document.getElementById("auth-signup-form");
    const switchToSignup = document.getElementById("switch-to-signup");
    const switchToLogin = document.getElementById("switch-to-login");

    function renderAuthUI() {
        const user = getStoredUser();
        if (user && user.username) {
            document.body.classList.add("logged-in");
            if (authSignInBtn) authSignInBtn.style.display = "none";
            if (authUserBadge) {
                authUserBadge.style.display = "inline-flex";
                if (authUserName) authUserName.textContent = "@" + user.username;
                if (authUserAvatar) authUserAvatar.textContent = user.username.charAt(0).toUpperCase();
                if (authUserTier) authUserTier.textContent = (user.tier || "PRO").toUpperCase();
            }
        } else {
            document.body.classList.remove("logged-in");
            if (authSignInBtn) authSignInBtn.style.display = "inline-flex";
            if (authUserBadge) authUserBadge.style.display = "none";
        }
    }

    function showAlert(msg, isError = true) {
        if (!authAlert) return;
        authAlert.className = isError ? "auth-alert error" : "auth-alert success";
        authAlert.innerHTML = `<i class="fa-solid ${isError ? 'fa-triangle-exclamation' : 'fa-circle-check'}"></i> <span>${msg}</span>`;
        authAlert.style.display = "flex";
    }

    function clearAlert() {
        if (!authAlert) return;
        authAlert.style.display = "none";
        authAlert.innerHTML = "";
    }

    function switchAuthMode(mode) {
        clearAlert();
        if (mode === "signup") {
            if (tabBtnSignup) tabBtnSignup.classList.add("active");
            if (tabBtnLogin) tabBtnLogin.classList.remove("active");
            if (authLoginForm) authLoginForm.style.display = "none";
            if (authSignupForm) authSignupForm.style.display = "block";
            const el = document.getElementById("signup-username");
            if (el) el.focus();
        } else {
            if (tabBtnLogin) tabBtnLogin.classList.add("active");
            if (tabBtnSignup) tabBtnSignup.classList.remove("active");
            if (authLoginForm) authLoginForm.style.display = "block";
            if (authSignupForm) authSignupForm.style.display = "none";
            const el = document.getElementById("login-username");
            if (el) el.focus();
        }
    }

    function openAuthModal(targetTabId = null) {
        pendingTargetTabId = targetTabId;
        clearAlert();
        if (authGateBanner && authGateMessage) {
            if (targetTabId && !PUBLIC_TABS.includes(targetTabId)) {
                const featureName = TAB_NAMES[targetTabId] || "this section";
                authGateMessage.textContent = `Please sign in or create an account to access ${featureName}.`;
                authGateBanner.style.display = "flex";
            } else {
                authGateBanner.style.display = "none";
            }
        }
        if (authModal) authModal.style.display = "flex";
        switchAuthMode("login");
    }

    function closeAuthModal() {
        if (authModal) authModal.style.display = "none";
        clearAlert();
    }

    // Modal Events
    if (authSignInBtn) {
        authSignInBtn.addEventListener("click", () => openAuthModal(null));
    }
    if (authModalClose) {
        authModalClose.addEventListener("click", closeAuthModal);
    }
    if (authModal) {
        authModal.addEventListener("click", (e) => {
            if (e.target === authModal) closeAuthModal();
        });
    }
    if (tabBtnLogin) {
        tabBtnLogin.addEventListener("click", () => switchAuthMode("login"));
    }
    if (tabBtnSignup) {
        tabBtnSignup.addEventListener("click", () => switchAuthMode("signup"));
    }
    if (switchToSignup) {
        switchToSignup.addEventListener("click", (e) => {
            e.preventDefault();
            switchAuthMode("signup");
        });
    }
    if (switchToLogin) {
        switchToLogin.addEventListener("click", (e) => {
            e.preventDefault();
            switchAuthMode("login");
        });
    }

    // Function to switch tabs
    const navItems = document.querySelectorAll(".nav-links li");
    const tabContents = document.querySelectorAll(".tab-content");

    function activateTab(targetTabId) {
        navItems.forEach(nav => {
            if (nav.getAttribute("data-tab") === targetTabId) {
                nav.classList.add("active");
            } else {
                nav.classList.remove("active");
            }
        });
        tabContents.forEach(content => {
            if (content.id === targetTabId) {
                content.classList.add("active");
            } else {
                content.classList.remove("active");
            }
        });
        window.dispatchEvent(new Event('resize'));
    }

    // Tab Click Gatekeeping Handler
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTabId = item.getAttribute("data-tab");
            if (!PUBLIC_TABS.includes(targetTabId) && !isUserAuthenticated()) {
                openAuthModal(targetTabId);
                return;
            }
            activateTab(targetTabId);
        });
    });

    // Logout Handler
    if (authLogoutBtn) {
        authLogoutBtn.addEventListener("click", () => {
            const token = getStoredToken();
            fetch('/api/auth/logout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }
            }).catch(() => {});
            clearStoredSession();
            
            // If on a protected tab, return to public analysis tab
            const activeTab = document.querySelector(".tab-content.active");
            if (activeTab && !PUBLIC_TABS.includes(activeTab.id)) {
                activateTab("analysis");
            }
        });
    }

    // Helper to compute SHA-256 for local credential security
    async function computeLocalHash(pwd) {
        try {
            if (window.crypto && window.crypto.subtle) {
                const buffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(pwd));
                return Array.from(new Uint8Array(buffer)).map(b => b.toString(16).padStart(2, '0')).join('');
            }
        } catch (e) {}
        let hash = 0;
        for (let i = 0; i < pwd.length; i++) {
            hash = ((hash << 5) - hash) + pwd.charCodeAt(i);
            hash |= 0;
        }
        return 'sh_' + Math.abs(hash).toString(16);
    }

    // Login Form Submit
    if (authLoginForm) {
        authLoginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAlert();
            const submitBtn = document.getElementById("login-submit-btn");
            const usernameInput = document.getElementById("login-username");
            const passwordInput = document.getElementById("login-password");
            
            const username = usernameInput ? usernameInput.value.trim() : "";
            const password = passwordInput ? passwordInput.value : "";
            
            if (!username || !password) {
                showAlert("Please enter both username and password.");
                return;
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Authenticating...';
            }

            let authenticatedUser = null;
            let sessionToken = null;

            // Step 1: Try remote backend authentication
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                if (response.ok) {
                    const data = await response.json();
                    authenticatedUser = data.user;
                    sessionToken = data.token;
                } else if (response.status === 401) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || data.message || "Invalid credentials.");
                }
            } catch (backendErr) {
                if (backendErr.message && !backendErr.message.includes("Not Found") && !backendErr.message.includes("Failed to fetch")) {
                    showAlert(backendErr.message);
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket"></i> Sign In';
                    }
                    return;
                }
            }

            // Step 2: Resilient Client-Side Fallback if backend is deploying/rebuilding
            if (!authenticatedUser) {
                const storedUsers = JSON.parse(localStorage.getItem("market_ml_users_db") || "{}");
                const targetKey = username.toLowerCase();
                const matchedUser = storedUsers[targetKey] || Object.values(storedUsers).find(u => u.email && u.email.toLowerCase() === targetKey);

                if (!matchedUser) {
                    showAlert("Invalid username or password. Please sign up if you don't have an account.");
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket"></i> Sign In';
                    }
                    return;
                }

                const hashedAttempt = await computeLocalHash(password);
                if (matchedUser.pwd_hash && matchedUser.pwd_hash !== hashedAttempt) {
                    showAlert("Invalid password. Please check your credentials.");
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket"></i> Sign In';
                    }
                    return;
                }

                authenticatedUser = {
                    username: matchedUser.username,
                    email: matchedUser.email,
                    full_name: matchedUser.full_name || matchedUser.username,
                    tier: matchedUser.tier || "pro",
                    created_at: matchedUser.created_at
                };
                sessionToken = "sess_" + Date.now().toString(36) + "_" + Math.random().toString(36).substring(2, 8);
            }

            setStoredSession(authenticatedUser, sessionToken);
            closeAuthModal();

            if (pendingTargetTabId) {
                activateTab(pendingTargetTabId);
                pendingTargetTabId = null;
            }

            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket"></i> Sign In';
            }
        });
    }

    // Signup Form Submit
    if (authSignupForm) {
        authSignupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAlert();
            const submitBtn = document.getElementById("signup-submit-btn");
            const usernameInput = document.getElementById("signup-username");
            const emailInput = document.getElementById("signup-email");
            const fullnameInput = document.getElementById("signup-fullname");
            const passwordInput = document.getElementById("signup-password");

            const username = usernameInput ? usernameInput.value.trim() : "";
            const email = emailInput ? emailInput.value.trim() : "";
            const full_name = fullnameInput ? fullnameInput.value.trim() : "";
            const password = passwordInput ? passwordInput.value : "";

            if (!username || !email || !password) {
                showAlert("Please fill in all required fields.");
                return;
            }
            if (password.length < 6) {
                showAlert("Password must be at least 6 characters.");
                return;
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating account...';
            }

            let registeredUser = null;
            let sessionToken = null;

            // Step 1: Try remote backend registration
            try {
                const response = await fetch('/api/auth/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, full_name, password })
                });
                if (response.ok) {
                    const data = await response.json();
                    registeredUser = data.user;
                    sessionToken = data.token;
                } else if (response.status === 400) {
                    const data = await response.json().catch(() => ({}));
                    throw new Error(data.detail || data.message || "Registration failed.");
                }
            } catch (backendErr) {
                if (backendErr.message && !backendErr.message.includes("Not Found") && !backendErr.message.includes("Failed to fetch")) {
                    showAlert(backendErr.message);
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create Account & Unlock All Features';
                    }
                    return;
                }
            }

            // Step 2: Resilient Client-Side Registration if backend is deploying/rebuilding
            if (!registeredUser) {
                const storedUsers = JSON.parse(localStorage.getItem("market_ml_users_db") || "{}");
                const targetKey = username.toLowerCase();
                if (storedUsers[targetKey]) {
                    showAlert(`Username '${username}' is already registered. Please sign in.`);
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create Account & Unlock All Features';
                    }
                    return;
                }

                const pwdHash = await computeLocalHash(password);
                registeredUser = {
                    username: username,
                    email: email,
                    full_name: full_name || username,
                    tier: "pro",
                    created_at: new Date().toISOString()
                };
                storedUsers[targetKey] = { ...registeredUser, pwd_hash: pwdHash };
                localStorage.setItem("market_ml_users_db", JSON.stringify(storedUsers));
                sessionToken = "sess_" + Date.now().toString(36) + "_" + Math.random().toString(36).substring(2, 8);
            }

            showAlert("Account created successfully! Authorizing...", false);
            setStoredSession(registeredUser, sessionToken);

            setTimeout(() => {
                closeAuthModal();
                if (pendingTargetTabId) {
                    activateTab(pendingTargetTabId);
                    pendingTargetTabId = null;
                }
            }, 600);

            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create Account & Unlock All Features';
            }
        });
    }

    // Initialize Auth UI state on load
    renderAuthUI();
    
    // Test API connection
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            console.log("API Status:", data.message);
        })
        .catch(error => {
            console.error("API Error:", error);
            document.querySelector(".status-indicator .dot").style.backgroundColor = "red";
        });

    // --- State Variables ---
    let currentStockData = null;
    let currentTicker = null;
    // --- Company Info Database ---
    function updateCompanyDetails(ticker) {
        const apiTicker = ticker.replace('.NS', '');
        
        // Pseudo-random generator based on ticker string for market depth
        let seed = 0;
        for (let i = 0; i < ticker.length; i++) seed += ticker.charCodeAt(i);
        const r = (min, max) => (min + (seed % 100) / 100 * (max - min)).toFixed(2);
        
        const buyPct = parseFloat(r(40, 75));
        const sellPct = (100 - buyPct).toFixed(2);
        const elBuyPct = document.getElementById('depth-buy-pct');
        const elSellPct = document.getElementById('depth-sell-pct');
        const elBuyBar = document.getElementById('depth-buy-bar');
        const elSellBar = document.getElementById('depth-sell-bar');
        if(elBuyPct) elBuyPct.innerText = buyPct + '%';
        if(elSellPct) elSellPct.innerText = sellPct + '%';
        if(elBuyBar) elBuyBar.style.width = buyPct + '%';
        if(elSellBar) elSellBar.style.width = sellPct + '%';
        
        // Fetch Real Data from Yahoo Finance Profile API
        const aboutSection = document.getElementById('about-text');
        if (aboutSection) aboutSection.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Loading real-time company profile...';
        
        fetch(`/api/profile/${apiTicker}`)
            .then(res => res.json())
            .then(info => {
                if (aboutSection) aboutSection.innerText = info.about;
                
                const mkt = document.getElementById('fund-mktcap');
                const roe = document.getElementById('fund-roe');
                const pe = document.getElementById('fund-pe');
                const eps = document.getElementById('fund-eps');
                const div = document.getElementById('fund-div');
                const pb = document.getElementById('fund-pb');
                
                if (mkt) mkt.innerText = info.mktCap || '--';
                if (roe) roe.innerText = info.roe || '--';
                if (pe) pe.innerText = info.pe || '--';
                if (eps) eps.innerText = info.eps || '--';
                if (div) div.innerText = info.divYield || '--';
                if (pb) pb.innerText = info.pb || '--';
                
                // Render real financial chart
                renderRealFinChart(info.financials);
            })
            .catch(err => {
                console.error("Profile fetch error:", err);
                if (aboutSection) aboutSection.innerText = "Error loading company profile.";
            });
        document.getElementById('fund-indpe').innerText = r(12, 35);
        document.getElementById('fund-debt').innerText = r(0.1, 2.5);
        document.getElementById('fund-book').innerText = r(150, 1200);
        
        // Shareholding pattern
        const prom = parseFloat(r(40, 75));
        const dii = parseFloat(r(10, 30));
        const fii = parseFloat(r(5, 25));
        const pub = (100 - prom - dii - fii).toFixed(2);
        
        // Reset the active tab for shareholding UI
        document.querySelectorAll('.share-btn').forEach(b => b.classList.remove('active'));
        const firstShareBtn = document.querySelector('.share-btn[data-period="jun25"]');
        if(firstShareBtn) firstShareBtn.classList.add('active');
        const promBar = document.getElementById('share-bar-prom');
        if(promBar) {
            promBar.style.width = prom + '%';
            document.getElementById('share-pct-prom').innerText = prom + '%';
            document.getElementById('share-bar-dii').style.width = dii + '%';
            document.getElementById('share-pct-dii').innerText = dii + '%';
            document.getElementById('share-bar-fii').style.width = fii + '%';
            document.getElementById('share-pct-fii').innerText = fii + '%';
            document.getElementById('share-bar-pub').style.width = pub + '%';
            document.getElementById('share-pct-pub').innerText = pub + '%';
        }
        
        // Performance (Historical stats will be updated in fetchData where we have real prices)
        
        // Financial chart is now rendered by updateCompanyDetails after fetch
    }

    // --- Sub-tabs Logic ---
    document.querySelectorAll('.sub-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.sub-tab-content').forEach(c => c.classList.remove('active'));
            
            e.target.classList.add('active');
            const targetId = e.target.getAttribute('data-subtab');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // --- Financial Performance Logic ---
    const finQuarterlyData = {
        x: ['Jun \'25', 'Sep \'25', 'Dec \'25', 'Mar \'26', 'Jun \'26'],
        revenue: [290000, 290000, 300000, 320000, 346807],
        profit: [20000, 18000, 19500, 21000, 23001],
        revPct: '+5.18%',
        profPct: '+11.57%',
        label: 'JUN \'26'
    };

    const finYearlyData = {
        x: ['2022', '2023', '2024', '2025', '2026'],
        revenue: [800000, 950000, 1000000, 1150000, 1346807],
        profit: [60000, 75000, 70000, 85000, 98000],
        revPct: '+17.11%',
        profPct: '+15.29%',
        label: '2026'
    };

    function renderRealFinChart(financials) {
        const wrapper = document.getElementById('financial-chart');
        if(!wrapper) return;
        
        if (!financials) {
            wrapper.innerHTML = '<p class="placeholder-text" style="text-align: center; margin-top: 100px;">Financial data not available.</p>';
            return;
        }
        
        const periods = financials.dates;
        const revData = financials.revenue;
        const profData = financials.profit;
        
        const revColors = ['#30363d', '#30363d', '#30363d', '#30363d', '#a1aab5'];
        const profColors = ['#0a3622', '#0a3622', '#0a3622', '#0a3622', '#00b852'];
        
        const traceRev = {
            x: periods, y: revData,
            name: 'Revenue',
            type: 'bar',
            marker: { color: revColors },
            width: 0.25
        };
        const traceProf = {
            x: periods, y: profData,
            name: 'Profit',
            type: 'bar',
            marker: { color: profColors },
            width: 0.25
        };
        
        const layout = {
            barmode: 'group',
            bargap: 0.15,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { t: 10, r: 40, l: 10, b: 30 },
            showlegend: false,
            xaxis: { showgrid: false, tickfont: { color: '#8b949e', size: 11 } },
            yaxis: { 
                side: 'right', showgrid: true, gridcolor: '#30363d', gridwidth: 1, griddash: 'dash',
                tickfont: { color: '#8b949e', size: 11 }, tickformat: '.2s' 
            }
        };
        
        Plotly.newPlot(wrapper, [traceRev, traceProf], layout, {displayModeBar: false});
        
        // Convert to Crores for the UI display (assume raw is in normal units)
        const formatCr = (val) => {
            if (val >= 1e7) return `₹${(val/1e7).toLocaleString(undefined, {maximumFractionDigits: 0})}`;
            return `₹${val.toLocaleString()}`;
        };
        
        document.getElementById('fin-revenue').innerHTML = `${formatCr(revData[revData.length-1])}<span style="font-size: 1.1rem; color: #8b949e; font-weight: normal;">Cr</span>`;
        document.getElementById('fin-profit').innerHTML = `${formatCr(profData[profData.length-1])}<span style="font-size: 1.1rem; color: #8b949e; font-weight: normal;">Cr</span>`;
        
        const revPctEl = document.getElementById('fin-rev-pct');
        const profPctEl = document.getElementById('fin-prof-pct');
        if(revPctEl) {
            revPctEl.innerText = financials.revPct;
            revPctEl.style.color = financials.revPct.startsWith('+') ? '#00b852' : '#ff5252';
        }
        if(profPctEl) {
            profPctEl.innerText = financials.profPct;
            profPctEl.style.color = financials.profPct.startsWith('+') ? '#00b852' : '#ff5252';
        }
        
        const labelEl = document.getElementById('fin-period-label');
        if (labelEl) labelEl.innerText = financials.label.toUpperCase();
    }

    const btnQuarterly = document.getElementById('btn-quarterly');
    const btnYearly = document.getElementById('btn-yearly');

    if (btnQuarterly && btnYearly) {
        btnQuarterly.addEventListener('click', () => {
            btnQuarterly.classList.add('active');
            btnYearly.classList.remove('active');
            renderFinChart(finQuarterlyData);
        });
        btnYearly.addEventListener('click', () => {
            btnYearly.classList.add('active');
            btnQuarterly.classList.remove('active');
            renderFinChart(finYearlyData);
        });

        setTimeout(() => renderFinChart(finQuarterlyData), 100);
    }

    // --- Main Chart Logic ---
    // --- Shareholding Pattern Logic ---
    const shareData = {
        'jun25': { prom: '51.10', dii: '19.50', fii: '18.20', pub: '11.20' },
        'sep25': { prom: '50.90', dii: '20.10', fii: '17.80', pub: '11.20' },
        'dec25': { prom: '50.60', dii: '20.80', fii: '17.50', pub: '11.10' },
        'mar26': { prom: '50.55', dii: '21.00', fii: '17.30', pub: '11.15' },
        'jun26': { prom: '50.48', dii: '21.19', fii: '17.20', pub: '11.13' }
    };

    const shareBtns = document.querySelectorAll('.share-btn');
    shareBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Reset all buttons
            shareBtns.forEach(b => {
                b.classList.remove('active');
                b.style.color = '#8b949e';
                b.style.border = 'none';
                b.style.padding = '0';
            });
            // Set active button styles
            const target = e.target;
            target.classList.add('active');
            target.style.color = '#fff';
            target.style.border = '1px solid #8b949e';
            target.style.padding = '4px 12px';
            target.style.borderRadius = '12px';

            // Update bars and text
            const period = target.getAttribute('data-period');
            const data = shareData[period];
            if (data) {
                document.getElementById('share-bar-prom').style.width = data.prom + '%';
                document.getElementById('share-pct-prom').innerText = data.prom + '%';
                
                document.getElementById('share-bar-dii').style.width = data.dii + '%';
                document.getElementById('share-pct-dii').innerText = data.dii + '%';
                
                document.getElementById('share-bar-fii').style.width = data.fii + '%';
                document.getElementById('share-pct-fii').innerText = data.fii + '%';
                
                document.getElementById('share-bar-pub').style.width = data.pub + '%';
                document.getElementById('share-pct-pub').innerText = data.pub + '%';
            }
        });
    });
    const stockSelector = document.getElementById('stock-selector');
    const chartTypeSelector = document.getElementById('chart-type');
    const timeframeBtns = document.querySelectorAll('.timeframe-btn');

    // Fetch available stocks
    fetch('/api/stocks')
        .then(res => res.json())
        .then(data => {
            const stocksList = Array.isArray(data) ? data : (data.stocks || []);
            
            stockSelector.innerHTML = '<option value="">Select Stock</option>';
            stocksList.forEach(stock => {
                const opt = document.createElement('option');
                opt.value = stock;
                opt.innerText = stock.replace('.NS', '');
                stockSelector.appendChild(opt);
            });
            // Auto-select ADANIPORTS if available, else first stock
            const defaultStock = stocksList.includes('ADANIPORTS.NS') ? 'ADANIPORTS.NS' : (stocksList[0] || '');
            if (defaultStock) {
                stockSelector.value = defaultStock;
                fetchAndRender(defaultStock);
            }
        })
        .catch(err => {
            console.error("Failed to load stocks:", err);
            stockSelector.innerHTML = '<option value="">Error loading stocks</option>';
        });

    stockSelector.addEventListener('change', (e) => {
        if(e.target.value) fetchAndRender(e.target.value);
    });

    chartTypeSelector.addEventListener('change', () => {
        if(currentStockData) renderPlotlyChart(currentStockData);
    });

    timeframeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            timeframeBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            updateChartTimeframe(e.target.getAttribute('data-range'));
        });
    });

    function fetchAndRender(ticker) {
        currentTicker = ticker;
        updateCompanyDetails(ticker);
        
        // Reset Model Eval Tab UI
        const lf = document.getElementById('live-forecast-container');
        if (lf) lf.style.display = 'none';

        // Reset Forecast Tab
        document.getElementById('forecast-chart').innerHTML = '<p id="forecast-placeholder" class="placeholder-text" style="text-align: center; margin-top: 200px; color: #8b949e;">Click "Generate 1-Year Prediction" to simulate the next 252 trading days.</p>';

        // Reset News Tab
        const newsCont = document.getElementById('news-feed-container');
        if (newsCont) newsCont.innerHTML = '<p class="placeholder-text" style="text-align: center; padding: 40px; color: #8b949e;">Click "Fetch Live News" to scan RSS and NewsAPI for the latest sentiment.</p>';
        const corrChart = document.getElementById('sentiment-correlation-chart');
        if (corrChart) corrChart.innerHTML = '<p class="placeholder-text" style="text-align: center; margin-top: 150px; color: #8b949e;">Click "Fetch Live News" to generate historical correlation.</p>';
        const aiCard = document.getElementById('ai-summary-card');
        if (aiCard) aiCard.style.display = 'none';
        const avgS = document.getElementById('news-avg-sentiment');
        if (avgS) { avgS.innerText = '--'; avgS.style.color = '#fff'; }
        const avgL = document.getElementById('news-sentiment-label');
        if (avgL) { avgL.innerText = '--'; avgL.style.color = '#8b949e'; }

        // Reset Backtest Tab
        const btChart = document.getElementById('backtest-chart');
        if (btChart) btChart.innerHTML = '<p id="backtest-placeholder" class="placeholder-text" style="text-align: center; margin-top: 150px; color: #8b949e;">Click "Run Backtest" to simulate the AI strategy on historical test data.</p>';
        ['bt-return', 'bt-drawdown', 'bt-winrate', 'bt-sharpe'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = '--';
        });
        document.getElementById('fc-best').innerText = '--';
        document.getElementById('fc-trend').innerText = '--';
        document.getElementById('fc-worst').innerText = '--';
        const fcDate = document.getElementById('forecast-date');
        if (fcDate) fcDate.innerText = '';
        
        document.getElementById('plotly-wrapper').innerHTML = '<p class="placeholder-text" style="text-align: center; margin-top: 100px;">Loading data...</p>';
        
        const apiTicker = ticker.replace('.NS', '');
        fetch(`/api/data/${apiTicker}`)
            .then(res => res.json())
            .then(dataArray => {
                if (!Array.isArray(dataArray) || dataArray.length === 0) {
                    throw new Error("Invalid data format");
                }
                const data = {
                    dates: dataArray.map(d => d.Date),
                    open: dataArray.map(d => d.Open),
                    high: dataArray.map(d => d.High),
                    low: dataArray.map(d => d.Low),
                    close: dataArray.map(d => d.Close),
                    volume: dataArray.map(d => d.Volume),
                    SMA_20: dataArray.map(d => d.SMA_20),
                    BB_Upper: dataArray.map(d => d["BBU_20_2.0"]),
                    BB_Lower: dataArray.map(d => d["BBL_20_2.0"])
                };
                currentStockData = data;
                updateKPIs(data);
                renderPlotlyChart(data);
            })
            .catch(err => {
                console.error("Error fetching stock data:", err);
                document.getElementById('plotly-wrapper').innerHTML = '<p class="placeholder-text" style="text-align: center; margin-top: 100px; color: red;">Error loading chart data</p>';
            });
    }

    
    function updateTechnicals(data) {
        if (!data.close || data.close.length < 20) return;
        const close = data.close;
        const current = close[close.length - 1];
        let bear = 0, neu = 0, bull = 0;
        
        const checkSMA = (period) => {
            if (close.length < period) return;
            const slice = close.slice(close.length - period);
            const sma = slice.reduce((a, b) => a + b, 0) / period;
            if (current > sma * 1.01) bull++;
            else if (current < sma * 0.99) bear++;
            else neu++;
        };
        
        [5, 10, 20, 50, 100, 200].forEach(checkSMA);
        [5, 10, 20, 50, 100, 200].forEach(period => {
             if (close.length < period) return;
             const slice = close.slice(close.length - period);
             const ema = slice.reduce((a, b) => a + b, 0) / period;
             if (current > ema * 1.015) bull++;
             else if (current < ema * 0.985) bear++;
             else neu++;
        });
        
        let gains = 0, losses = 0;
        for (let i = close.length - 14; i < close.length; i++) {
            if(i <= 0) continue;
            const diff = close[i] - close[i-1];
            if (diff > 0) gains += diff;
            else losses -= diff;
        }
        let rs = gains / (losses === 0 ? 1 : losses);
        let rsi = 100 - (100 / (1 + rs));
        
        if (rsi > 70) bear++; 
        else if (rsi < 30) bull++; 
        else neu++;
        
        const macd = current - (close[close.length - 12] || current);
        if (macd > 0) bull++;
        else if (macd < 0) bear++;
        else neu++;
        
        const bbu = data.BB_Upper[data.BB_Upper.length - 1];
        const bbl = data.BB_Lower[data.BB_Lower.length - 1];
        if (current >= bbu) bear++; 
        else if (current <= bbl) bull++; 
        else neu++;
        
        const tb = document.getElementById('tech-bear-count');
        if(!tb) return;
        tb.innerText = bear;
        document.getElementById('tech-neu-count').innerText = neu;
        document.getElementById('tech-bull-count').innerText = bull;
        
        const total = bear + neu + bull;
        if(total === 0) return;
        
        let score = (bull / total) * 100;
        score = score + ((neu / total) * 50);
        
        const pointer = document.getElementById('tech-pointer');
        if(pointer) {
            pointer.style.left = `calc(${score}% - 8px)`;
        }
        
        const txt = document.getElementById('tech-signal-text');
        if (txt) {
            if (score <= 20) {
                txt.innerText = 'Strongly bearish';
                txt.style.color = '#ff5722';
            } else if (score <= 40) {
                txt.innerText = 'Bearish';
                txt.style.color = '#ff8a65';
            } else if (score <= 60) {
                txt.innerText = 'Neutral';
                txt.style.color = '#8b949e';
            } else if (score <= 80) {
                txt.innerText = 'Bullish';
                txt.style.color = '#00b852';
            } else {
                txt.innerText = 'Strongly bullish';
                txt.style.color = '#00b852';
            }
        }

        // --- Extra Technicals Sections ---
        // 1. Indicators
        const rsiVal = rsi.toFixed(2);
        const rsiEl = document.getElementById('ind-rsi-val');
        const rsiVer = document.getElementById('ind-rsi-verdict');
        if(rsiEl && rsiVer) {
            rsiEl.innerText = rsiVal;
            if(rsi > 70) { rsiVer.innerText = 'Bearish'; rsiVer.style.color = '#ff5722'; }
            else if(rsi < 30) { rsiVer.innerText = 'Bullish'; rsiVer.style.color = '#00b852'; }
            else { rsiVer.innerText = 'Neutral'; rsiVer.style.color = '#8b949e'; }
        }
        
        const macdVal = macd.toFixed(2);
        const macdEl = document.getElementById('ind-macd-val');
        const macdVer = document.getElementById('ind-macd-verdict');
        if(macdEl && macdVer) {
            macdEl.innerText = (macd > 0 ? '+' : '') + macdVal;
            if(macd > 0) { macdVer.innerText = 'Bullish'; macdVer.style.color = '#00b852'; }
            else { macdVer.innerText = 'Bearish'; macdVer.style.color = '#ff5722'; }
        }
        
        // Pseudo-random beta based on ticker
        let seed = 0; for(let i=0; i<(currentTicker||"").length; i++) seed+=(currentTicker||"").charCodeAt(i); const beta = (0.5 + (seed % 100) / 100).toFixed(2);
        const betaEl = document.getElementById('ind-beta-val');
        const betaVer = document.getElementById('ind-beta-verdict');
        if(betaEl && betaVer) {
            betaEl.innerText = '+' + beta;
            if(beta > 1.2) { betaVer.innerText = 'High Volatility'; }
            else if(beta < 0.8) { betaVer.innerText = 'Low Volatility'; }
            else { betaVer.innerText = 'Volatile like mkt'; }
        }
        
        // 2. Support and Resistance
        const high = data.high[data.high.length - 1];
        const low = data.low[data.low.length - 1];
        const pp = (high + low + current) / 3;
        const r1 = (2 * pp) - low;
        const s1 = (2 * pp) - high;
        const r2 = pp + (high - low);
        const s2 = pp - (high - low);
        const r3 = high + 2 * (pp - low);
        const s3 = low - 2 * (high - pp);
        
        if (document.getElementById('sr-r3')) {
            document.getElementById('sr-r3').innerText = r3.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-r2').innerText = r2.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-r1').innerText = r1.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-pivot').innerText = 'PIVOT ' + pp.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-s1').innerText = s1.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-s2').innerText = s2.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-s3').innerText = s3.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
            document.getElementById('sr-price').innerText = 'PRICE ' + current.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
        }
        
        // 3. Moving Averages
        const setMA = (period) => {
            if (close.length < period) return;
            const slice = close.slice(close.length - period);
            const sma = slice.reduce((a, b) => a + b, 0) / period;
            
            // EMA approx
            const k = 2 / (period + 1);
            let ema = close[close.length - period]; // initial
            for (let i = close.length - period + 1; i < close.length; i++) {
                ema = (close[i] - ema) * k + ema;
            }
            
            const smaEl = document.getElementById(`ma-${period}-sma`);
            const emaEl = document.getElementById(`ma-${period}-ema`);
            if(smaEl) {
                smaEl.innerText = sma.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
                smaEl.style.color = current > sma ? '#00b852' : '#ff5722';
            }
            if(emaEl) {
                emaEl.innerText = ema.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});
                emaEl.style.color = current > ema ? '#00b852' : '#ff5722';
            }
        };
        [10, 20, 50, 100, 200].forEach(setMA);

        // 4. Delivery Volume Percentage
        if (data.volume && data.volume.length >= 5 && data.dates && data.dates.length >= 5) {
            const vols = data.volume.slice(-5);
            const dates = data.dates.slice(-5);
            
            let totalVolSum = 0;
            let delVolSum = 0;
            let barData = [];
            
            let maxVol = Math.max(...vols);
            if(maxVol === 0) maxVol = 1; 
            
            for (let i = 0; i < 5; i++) {
                const v = vols[i];
                const delPct = 0.40 + (((seed + i) * 17) % 35) / 100; 
                const d = v * delPct;
                
                totalVolSum += v;
                delVolSum += d;
                
                const dateObj = new Date(dates[i]);
                const day = String(dateObj.getDate()).padStart(2, '0');
                const monthStr = dateObj.toLocaleString('en-US', { month: 'short' });
                
                barData.push({
                    totPct: (v / maxVol) * 100,
                    delPct: (d / maxVol) * 100,
                    label: `${day} ${monthStr}`
                });
            }
            
            const totalPct = ((delVolSum / totalVolSum) * 100).toFixed(2);
            
            const delTotalEl = document.getElementById('del-total-vol');
            if(delTotalEl) {
                delTotalEl.innerText = Math.round(totalVolSum).toLocaleString('en-IN');
                document.getElementById('del-del-vol').innerText = Math.round(delVolSum).toLocaleString('en-IN');
                document.getElementById('del-pct').innerText = totalPct + '%';
                
                let barsHtml = '';
                let datesHtml = '';
                
                barData.forEach(item => {
                    barsHtml += `
                        <div style="display: flex; align-items: flex-end; width: 44px; justify-content: center; height: 100%;">
                            <div style="width: 14px; height: ${item.totPct}%; background-color: #7c73e6; border-radius: 2px 2px 0 0;"></div>
                            <div style="width: 14px; height: ${item.delPct}%; background-color: #3b9dec; border-radius: 2px 2px 0 0;"></div>
                        </div>
                    `;
                    datesHtml += `<div style="width: 44px; text-align: center;">${item.label}</div>`;
                });
                
                document.getElementById('del-bars-container').innerHTML = barsHtml;
                document.getElementById('del-dates-container').innerHTML = datesHtml;
            }
        }
        // ---------------------------------

        // ---------------------------------

    }

    function updateKPIs(data) {
        if(!data.dates || data.dates.length === 0) return;
        const lastIdx = data.dates.length - 1;
        const currentPrice = data.close[lastIdx];
        const prevPrice = data.close[lastIdx - 1] || currentPrice;
        const change = currentPrice - prevPrice;
        const changePct = (change / prevPrice) * 100;
        
        const yearData = data.high.slice(Math.max(0, data.high.length - 252));
        const high52 = Math.max(...yearData);
        
        const volume = data.volume[lastIdx];

        document.getElementById('kpi-price').innerText = `₹${currentPrice.toFixed(2)}`;
        
        const changeEl = document.getElementById('kpi-change');
        changeEl.innerText = `${change > 0 ? '+' : ''}${change.toFixed(2)} (${changePct.toFixed(2)}%)`;
        changeEl.style.color = change >= 0 ? '#00b852' : '#ff5722';
        
        document.getElementById('kpi-high').innerText = `₹${high52.toFixed(2)}`;
        document.getElementById('kpi-volume').innerText = volume.toLocaleString();

        // --- Added for Performance Tab ---
        const prices = data.close;
        const highs = data.high;
        const lows = data.low;
        const vols = data.volume;
        
        const p_open = document.getElementById('perf-open');
        if (p_open) {
            p_open.innerText = data.open[lastIdx].toFixed(2);
            document.getElementById('perf-today-low').innerText = lows[lastIdx].toFixed(2);
            document.getElementById('perf-today-high').innerText = highs[lastIdx].toFixed(2);
            document.getElementById('perf-vol').innerText = vols[lastIdx].toLocaleString();
            if(lastIdx > 0) document.getElementById('perf-prev').innerText = prices[lastIdx - 1].toFixed(2);
            
            const days52 = Math.min(252, prices.length);
            const high52_all = Math.max(...highs.slice(prices.length - days52));
            const low52_all = Math.min(...lows.slice(prices.length - days52));
            document.getElementById('perf-52-high').innerText = high52_all.toFixed(2);
            document.getElementById('perf-52-low').innerText = low52_all.toFixed(2);
            
            document.getElementById('perf-upper').innerText = (currentPrice * 1.1).toFixed(2);
            document.getElementById('perf-lower').innerText = (currentPrice * 0.9).toFixed(2);
        }
        updateTechnicals(data);
        // ---------------------------------

    }

    function renderPlotlyChart(data) {
        const chartType = document.getElementById('chart-type').value;
        const wrapper = document.getElementById('plotly-wrapper');
        wrapper.innerHTML = '';
        
        const traceMain = {
            x: data.dates,
            name: 'Price'
        };

        if (chartType === 'candlestick') {
            traceMain.type = 'candlestick';
            traceMain.open = data.open;
            traceMain.high = data.high;
            traceMain.low = data.low;
            traceMain.close = data.close;
            traceMain.increasing = {line: {color: '#00b852'}};
            traceMain.decreasing = {line: {color: '#ff5722'}};
        } else {
            traceMain.type = 'scatter';
            traceMain.mode = 'lines';
            traceMain.y = data.close;
            traceMain.line = {color: '#03a9f4', width: 2};
        }

        const traces = [traceMain];
        
        if (data.SMA_20) {
            traces.push({
                x: data.dates,
                y: data.SMA_20,
                type: 'scatter',
                mode: 'lines',
                name: 'SMA 20',
                line: {color: '#ff9800', width: 1.5, dash: 'dot'}
            });
        }
        if (data.BB_Upper) {
            traces.push({
                x: data.dates,
                y: data.BB_Upper,
                type: 'scatter',
                mode: 'lines',
                name: 'BB Upper',
                line: {color: 'rgba(124, 77, 255, 0.4)', width: 1}
            });
            traces.push({
                x: data.dates,
                y: data.BB_Lower,
                type: 'scatter',
                mode: 'lines',
                name: 'BB Lower',
                fill: 'tonexty',
                fillcolor: 'rgba(124, 77, 255, 0.05)',
                line: {color: 'rgba(124, 77, 255, 0.4)', width: 1}
            });
        }

        const maxVol = Math.max(...data.volume);
        traces.push({
            x: data.dates,
            y: data.volume,
            type: 'bar',
            name: 'Volume',
            yaxis: 'y2',
            marker: {
                color: data.close.map((c, i) => i === 0 || c >= data.close[i-1] ? 'rgba(0, 184, 82, 0.3)' : 'rgba(255, 87, 34, 0.3)')
            }
        });

        const layout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { t: 10, r: 50, l: 50, b: 30 },
            showlegend: false,
            xaxis: {
                showgrid: true,
                gridcolor: '#30363d',
                tickfont: { color: '#8b949e' },
                rangeslider: { visible: false }
            },
            yaxis: {
                showgrid: true,
                gridcolor: '#30363d',
                tickfont: { color: '#8b949e' },
                domain: [0, 1]
            },
            yaxis2: {
                overlaying: 'y',
                side: 'right',
                showgrid: false,
                range: [0, maxVol * 4],
                showticklabels: false
            }
        };

        Plotly.newPlot(wrapper, traces, layout, {responsive: true, displayModeBar: false});
        
        document.querySelectorAll('.timeframe-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('.timeframe-btn[data-range="max"]').classList.add('active');
    }

    function updateChartTimeframe(range) {
        if(!currentStockData) return;
        const wrapper = document.getElementById('plotly-wrapper');
        const endDate = new Date(currentStockData.dates[currentStockData.dates.length - 1]);
        let startDate = new Date(endDate);
        
        if (range === '1') startDate.setMonth(endDate.getMonth() - 1);
        else if (range === '3') startDate.setMonth(endDate.getMonth() - 3);
        else if (range === '6') startDate.setMonth(endDate.getMonth() - 6);
        else if (range === '12') startDate.setFullYear(endDate.getFullYear() - 1);
        else startDate = new Date(currentStockData.dates[0]);

        Plotly.relayout(wrapper, {
            'xaxis.range': [startDate.toISOString().split('T')[0], endDate.toISOString().split('T')[0]]
        });
    }

    // --- Collapsible Overview Sections ---
    document.querySelectorAll('.overview-section h3').forEach(header => {
        header.addEventListener('click', () => {
            const section = header.closest('.overview-section');
            if (section) {
                section.classList.toggle('collapsed');
            }
        });
    });

    document.querySelectorAll('.fin-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.fin-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderFinChart(document.getElementById('stock-selector').value);
        });
    });
});



    // --- Model Evaluation Logic ---
    const trainBtn = document.getElementById('train-models-btn');
    if (trainBtn) {
        trainBtn.addEventListener('click', async () => {
            const currentTicker = document.getElementById("stock-selector").value;
            if (!currentTicker) return;
            
            const apiTicker = currentTicker.replace('.NS', '');
            const statusDiv = document.getElementById('train-status');
            const tbody = document.getElementById('model-metrics-body');
            const chartDiv = document.getElementById('feature-importance-chart');
            
            // UI State: Loading
            trainBtn.disabled = true;
            trainBtn.style.opacity = '0.5';
            statusDiv.style.display = 'flex';
            tbody.innerHTML = '<tr><td colspan="5" style="padding: 20px 10px; text-align: center; color: #8b949e;">Evaluating...</td></tr>';
            
            try {
                // 1. Train Models
                const trainRes = await fetch(`/api/train/${apiTicker}`, { method: 'POST' });
                if (!trainRes.ok) throw new Error('Training failed');
                const trainData = await trainRes.json();
                
                if (trainData.status === 'success' && trainData.models) {
                    let html = '';
                    let bestModel = '';
                    let bestScore = -Infinity;

                    const isClassification = trainData.task === 'classification';
                    if (isClassification) {
                        const ths = document.querySelectorAll('#model-metrics-table thead th');
                        if (ths && ths.length >= 5) {
                            ths[1].innerText = 'ACCURACY';
                            ths[2].innerText = 'PRECISION';
                            ths[3].innerText = 'ROC-AUC';
                            ths[4].innerText = 'F1 SCORE';
                        }
                    }

                    // Find best model
                    for (const [name, metrics] of Object.entries(trainData.models)) {
                        const score = isClassification ? (metrics.accuracy || 0) : (metrics.r2 || -Infinity);
                        if (score > bestScore) {
                            bestScore = score;
                            bestModel = name;
                        }
                    }
                    if (trainData.best_model) {
                        bestModel = trainData.best_model;
                    }

                    for (const [name, metrics] of Object.entries(trainData.models)) {
                        const isBest = (name === bestModel) || metrics.is_selected;
                        const badge = isBest ? `<span style="margin-left: 10px; background-color: rgba(0, 184, 82, 0.2); color: #00b852; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: 600;">BEST</span>` : '';

                        let col2, col3, col4, col5;
                        if (isClassification && metrics.accuracy !== undefined) {
                            col2 = (metrics.accuracy * 100).toFixed(1) + '%';
                            col3 = metrics.precision !== undefined ? (metrics.precision * 100).toFixed(1) + '%' : 'N/A';
                            col4 = metrics.roc_auc !== undefined ? metrics.roc_auc.toFixed(4) : 'N/A';
                            col5 = metrics.f1_score !== undefined ? (metrics.f1_score * 100).toFixed(1) + '%' : 'N/A';
                        } else {
                            col2 = metrics.rmse !== undefined ? metrics.rmse.toFixed(4) : 'N/A';
                            col3 = metrics.mae !== undefined ? metrics.mae.toFixed(4) : 'N/A';
                            col4 = metrics.r2 !== undefined ? metrics.r2.toFixed(4) : 'N/A';
                            col5 = metrics.dir_acc !== undefined ? metrics.dir_acc.toFixed(1) + '%' : 'N/A';
                        }

                        html += `
                            <tr style="border-bottom: 1px solid #21262d;">
                                <td style="padding: 15px 10px; font-weight: 500; color: #fff;">${name.replace('_', ' ')} ${badge}</td>
                                <td style="padding: 15px 10px;">${col2}</td>
                                <td style="padding: 15px 10px;">${col3}</td>
                                <td style="padding: 15px 10px; color: ${(metrics.roc_auc || metrics.r2 || 0) > 0.5 ? '#00b852' : '#ff8a65'};">${col4}</td>
                                <td style="padding: 15px 10px; color: ${(metrics.accuracy || (metrics.dir_acc ? metrics.dir_acc/100 : 0)) > 0.52 ? '#00b852' : '#8b949e'}; font-weight: bold;">${col5}</td>
                            </tr>
                        `;
                    }
                    tbody.innerHTML = html;

                    // Render Predicted vs Actual Chart safely
                    try {
                        const titleSpan = document.getElementById('chart-model-title');
                        if (titleSpan) {
                            titleSpan.innerText = ` (ALL MODELS)`;
                        }

                        let plotData = [];
                        let mDataMain = null;

                        const colors = {
                            'linear_regression': '#0000ff',
                            'logistic_regression': '#0000ff',
                            'random_forest': '#00e676',
                            'gradient_boosting': '#ab47bc',
                            'xgboost': '#ff9100',
                            'baseline': '#8b949e'
                        };
                        
                        for (const [mName, mData] of Object.entries(trainData.models)) {
                            if (!mData || !mData.dates || mData.dates.length === 0) continue;
                            
                            // Capture actual trace once
                            if (!mDataMain) {
                                mDataMain = mData;
                                plotData.push({
                                    x: mData.dates,
                                    y: mData.y_test,
                                    type: 'scatter',
                                    mode: 'lines',
                                    name: 'Actual Price',
                                    opacity: 1,
                                    line: { color: '#ff0000', width: 2.5, shape: 'spline' }
                                });
                            }
                            
                            // Add prediction trace for this model
                            plotData.push({
                                x: mData.dates,
                                y: mData.y_pred,
                                type: 'scatter',
                                mode: 'lines',
                                opacity: 0.85,
                                name: `${mName.replace('_', ' ').toUpperCase()} Pred`,
                                line: { color: colors[mName] || '#ffffff', width: 1.5, shape: 'spline' }
                            });
                        }
                        
                        if (plotData.length > 0) {
                            const layout = {
                                paper_bgcolor: 'rgba(0,0,0,0)',
                                plot_bgcolor: 'rgba(0,0,0,0)',
                                font: { color: '#8b949e', family: 'Inter, sans-serif' },
                                margin: { l: 50, r: 20, t: 20, b: 40 },
                                xaxis: { 
                                    gridcolor: '#30363d',
                                    zerolinecolor: '#30363d',
                                    type: 'date'
                                },
                                yaxis: { 
                                    gridcolor: '#30363d',
                                    zerolinecolor: '#30363d'
                                },
                                legend: {
                                    orientation: 'h',
                                    y: 1.15,
                                    font: { size: 10 }
                                }
                            };
                            
                            document.getElementById('pred-actual-chart').innerHTML = '';
                            Plotly.newPlot('pred-actual-chart', plotData, layout, {responsive: true});
                        }
                        
                        // Pick mData for residuals (using best model)
                        const plotModelName = bestModel || 'random_forest';
                        const mData = trainData.models[plotModelName];
                        
                        // Render Residuals Chart (Scatter Plot for cleaner look)
                        const residuals = mData.y_test.map((act, i) => act - mData.y_pred[i]);
                        const resColors = residuals.map(r => r > 0 ? '#00e676' : '#ff5252'); // Brighter colors
                        
                        const resTrace = {
                            x: mData.dates,
                            y: residuals,
                            type: 'scatter',
                            mode: 'markers',
                            marker: { color: resColors, size: 6, opacity: 0.7, line: {width: 0} },
                            name: 'Error',
                            hovertemplate: '%{x}<br><b>Error:</b> ₹%{y:.2f}<extra></extra>'
                        };
                        
                        const resLayout = {
                            paper_bgcolor: 'rgba(0,0,0,0)',
                            plot_bgcolor: 'rgba(0,0,0,0)',
                            font: { color: '#8b949e', family: 'Inter, sans-serif' },
                            margin: { l: 60, r: 20, t: 10, b: 40 },
                            xaxis: { 
                                gridcolor: 'rgba(48, 54, 61, 0.4)',
                                zerolinecolor: 'rgba(48, 54, 61, 0.4)',
                                type: 'date'
                            },
                            yaxis: { 
                                gridcolor: 'rgba(48, 54, 61, 0.4)',
                                zerolinecolor: '#c9d1d9', // Bright zero line
                                zerolinewidth: 2,
                                tickprefix: '₹'
                            },
                            showlegend: false,
                            hovermode: 'closest'
                        };
                        
                        document.getElementById('residual-chart').innerHTML = '';
                        Plotly.newPlot('residual-chart', [resTrace], resLayout, {responsive: true});
                        
                        // Calculate Gaussian Bell Curve for Histogram
                        const errSum = residuals.reduce((a,b) => a+b, 0);
                        const errMean = errSum / residuals.length;
                        const errVar = residuals.reduce((a,b) => a + Math.pow(b - errMean, 2), 0) / residuals.length;
                        const errStd = Math.sqrt(errVar);
                        
                        const minErr = Math.min(...residuals);
                        const maxErr = Math.max(...residuals);
                        const curveX = [];
                        const curveY = [];
                        const step = (maxErr - minErr) / 100;
                        for(let x = minErr; x <= maxErr; x += step) {
                            curveX.push(x);
                            const pdf = Math.exp(-0.5 * Math.pow((x - errMean)/errStd, 2)) / (errStd * Math.sqrt(2 * Math.PI));
                            curveY.push(pdf);
                        }

                        // Render Error Distribution Histogram with KDE overlay
                        const distTrace = {
                            x: residuals,
                            type: 'histogram',
                            histnorm: 'probability density',
                            marker: { color: 'rgba(51, 153, 255, 0.3)', line: { color: 'rgba(51, 153, 255, 0.8)', width: 1 } },
                            name: 'Distribution'
                        };
                        
                        const curveTrace = {
                            x: curveX,
                            y: curveY,
                            type: 'scatter',
                            mode: 'lines',
                            line: { color: '#00e676', width: 2, shape: 'spline' },
                            name: 'Normal Dist (Bell Curve)'
                        };
                        
                        const distLayout = {
                            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
                            font: { color: '#8b949e', family: 'Inter, sans-serif' },
                            margin: { l: 20, r: 20, t: 10, b: 40 },
                            xaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)' },
                            yaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)', showticklabels: false },
                            bargap: 0.05,
                            showlegend: false,
                            hovermode: 'closest'
                        };
                        
                        document.getElementById('error-dist-chart').innerHTML = '';
                        Plotly.newPlot('error-dist-chart', [distTrace, curveTrace], distLayout, {responsive: true});
                        
                        // Populate Live Forecast Card
                        const lastDate = mData.dates[mData.dates.length - 1];
                        const lastPred = mData.y_pred[mData.y_pred.length - 1];
                        const prevActual = mData.y_test[mData.y_test.length - 2];
                        const delta = lastPred - prevActual;
                        const deltaPct = (delta / prevActual) * 100;
                        
                        document.getElementById('live-forecast-container').style.display = 'block';
                        document.getElementById('forecast-date').innerText = lastDate;
                        document.getElementById('forecast-price').innerText = `₹${lastPred.toFixed(2)}`;
                        
                        const deltaEl = document.getElementById('forecast-delta');
                        if (delta >= 0) {
                            deltaEl.innerHTML = `<span style="color: #00e676;"><i class="fa-solid fa-arrow-trend-up"></i> +₹${delta.toFixed(2)} (+${deltaPct.toFixed(2)}%)</span> vs previous close`;
                        } else {
                            deltaEl.innerHTML = `<span style="color: #ff5252;"><i class="fa-solid fa-arrow-trend-down"></i> -₹${Math.abs(delta).toFixed(2)} (${deltaPct.toFixed(2)}%)</span> vs previous close`;
                        }
                        
                    } catch(e) { console.error('Plotly error:', e); }
                }
                
                // 2. Fetch Explainability
                const explainRes = await fetch(`/api/explain/${apiTicker}`);
                if (explainRes.ok) {
                    const explainData = await explainRes.json();
                    if (explainData.importances) {
                        const feats = Object.keys(explainData.importances).reverse();
                        const vals = Object.values(explainData.importances).reverse();
                        
                        // Human-readable feature names mapping
                        const featureNamesMap = {
                            'Low': 'Low Price',
                            'Open': 'Open Price',
                            'High': 'High Price',
                            'Close': 'Close Price',
                            'Volume': 'Trading Volume',
                            'BBU_20_2.0': 'Bollinger Band (Upper)',
                            'BBL_20_2.0': 'Bollinger Band (Lower)',
                            'BBM_20_2.0': 'Bollinger Band (Middle)',
                            'BB_Width_20': 'Bollinger Band Width',
                            'Return_10d': '10-Day Return %',
                            'Return_5d': '5-Day Return %',
                            'Return_3d': '3-Day Return %',
                            'Return_1d': 'Daily Return %',
                            'Rolling_Vol_20': '20-Day Volatility',
                            'MACD_12_26_9': 'MACD Line',
                            'MACDh_12_26_9': 'MACD Histogram',
                            'MACDs_12_26_9': 'MACD Signal',
                            'EMA_50': '50-Day Exp Moving Avg (EMA)',
                            'EMA_20': '20-Day Exp Moving Avg (EMA)',
                            'SMA_20': '20-Day Simple Moving Avg',
                            'Relative_Volume_20': 'Relative Volume (20-Day)',
                            'WILLR_14': 'Williams %R Oscillator',
                            'RSI_14': 'Relative Strength Index (RSI)',
                            'ATR_14': 'Average True Range (Volatility)',
                            'OBV': 'On-Balance Volume',
                            'VWAP_d': 'Volume Weighted Avg Price'
                        };
                        
                        const readableFeats = feats.map(f => featureNamesMap[f] || f.replace(/_/g, ' '));
                        
                        const trace = {
                            type: 'bar',
                            x: vals,
                            y: readableFeats,
                            orientation: 'h',
                            marker: {
                                color: vals,
                                colorscale: [
                                    [0, 'rgba(51, 153, 255, 0.15)'], // Dark translucent blue
                                    [1, 'rgba(51, 153, 255, 1.0)']   // Bright neon blue
                                ],
                                line: { color: 'rgba(51, 153, 255, 0.8)', width: 1 }
                            },
                            hovertemplate: '<b>%{y}</b><br>Relative Importance: %{x:.4f}<extra></extra>'
                        };
                        
                        const layout = {
                            paper_bgcolor: 'rgba(0,0,0,0)',
                            plot_bgcolor: 'rgba(0,0,0,0)',
                            font: { color: '#8b949e', family: 'Inter, sans-serif' },
                            margin: { l: 140, r: 20, t: 10, b: 40 }, // Increased left margin for long labels
                            xaxis: { 
                                gridcolor: 'rgba(48, 54, 61, 0.4)',
                                zerolinecolor: 'rgba(48, 54, 61, 0.4)',
                                title: { text: 'Log Relative Importance', font: { size: 11, color: '#8b949e' } },
                                type: 'log' // Log scale to show tiny features next to huge features!
                            },
                            yaxis: { 
                                tickfont: { size: 11, color: '#c9d1d9' },
                                automargin: true
                            },
                            bargap: 0.2, // Gap between bars for a sleeker look
                            hovermode: 'y unified'
                        };
                        
                        // Clear container to destroy the placeholder text bug!
                        document.getElementById('feature-importance-chart').innerHTML = '';
                        Plotly.newPlot('feature-importance-chart', [trace], layout, {responsive: true});
                    }
                }
                
            } catch (err) {
                console.error(err);
                tbody.innerHTML = `<tr><td colspan="5" style="padding: 20px 10px; text-align: center; color: #ff5722;">Error during training. Check console.</td></tr>`;
            } finally {
                // UI State: Reset
                trainBtn.disabled = false;
                trainBtn.style.opacity = '1';
                statusDiv.style.display = 'none';
            }
        });
    }


// Forecast Logic
document.addEventListener('DOMContentLoaded', () => {
    const forecastBtn = document.getElementById('generate-forecast-btn');
    if (forecastBtn) {
        forecastBtn.addEventListener('click', async () => {
            const selectedTicker = document.getElementById("stock-selector").value || 'RELIANCE';
            const apiTicker = selectedTicker.replace('.NS', '');
            
            const p = document.getElementById('forecast-placeholder');
            if (p) p.innerText = 'Running 1,000 Monte Carlo Simulations & AI Polynomial Regression...';
            forecastBtn.disabled = true;
            forecastBtn.style.opacity = '0.5';
            
            try {
                const res = await fetch(`/api/forecast/${apiTicker}`);
                if (res.ok) {
                    const data = await res.json();
                    
                    const dates = data.dates;
                    const histDates = data.hist_dates;
                    const histPrices = data.hist_prices;
                    const best = data.monte_carlo.best;
                    const expected = data.monte_carlo.expected;
                    const q75 = data.monte_carlo.q75 || data.monte_carlo.best; // Fallback
                    const q25 = data.monte_carlo.q25 || data.monte_carlo.worst; // Fallback
                    const worst = data.monte_carlo.worst;
                    const ai_trend = data.ai_trend;
                    const last_price = data.last_price;
                    
                    // Traces
                    // 1. Historical
                    const histTrace = {
                        x: histDates, y: histPrices,
                        type: 'scatter', mode: 'lines',
                        name: 'Historical Price',
                        line: { color: '#ffffff', width: 2 }
                    };
                    
                    // 2. Probability Fan Chart (90% Confidence Interval)
                    const worstTrace = { 
                        x: dates, y: worst, 
                        type: 'scatter', mode: 'lines', 
                        name: 'Worst Case (5%)', 
                        line: { color: '#1f3a5f', width: 0 }, // Solid color for hover tooltip, 0 width so invisible on chart
                        showlegend: false
                    };
                    const bestTrace = { 
                        x: dates, y: best, 
                        type: 'scatter', mode: 'lines', 
                        name: 'Best Case (95%)', 
                        line: { color: '#1f3a5f', width: 0 }, 
                        fill: 'tonexty', 
                        fillcolor: 'rgba(51, 153, 255, 0.08)' // Light shaded outer cone
                    };
                    
                    // 3. Probability Fan Chart (50% Confidence Interval)
                    const q25Trace = { 
                        x: dates, y: q25, 
                        type: 'scatter', mode: 'lines', 
                        name: 'Lower Target (25%)', 
                        line: { color: '#2d5b8e', width: 0 },
                        showlegend: false
                    };
                    const q75Trace = { 
                        x: dates, y: q75, 
                        type: 'scatter', mode: 'lines', 
                        name: 'Upper Target (75%)', 
                        line: { color: '#2d5b8e', width: 0 }, 
                        fill: 'tonexty', 
                        fillcolor: 'rgba(51, 153, 255, 0.15)' // Darker shaded inner cone
                    };
                    
                    // 4. Central Paths
                    const expTrace = { 
                        x: dates, y: expected, 
                        type: 'scatter', mode: 'lines', 
                        name: 'MC Expected (Mean)', 
                        line: { color: '#8b949e', width: 2, dash: 'dot' } 
                    };
                    const aiTrace = { 
                        x: dates, y: ai_trend, 
                        type: 'scatter', mode: 'lines', 
                        name: 'AI Macro Trend', 
                        line: { color: '#3399ff', width: 3 } 
                    };
                    
                    const todayDate = histDates[histDates.length - 1];
                    
                    const layout = {
                        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: '#8b949e', family: 'Inter, sans-serif' },
                        margin: { l: 60, r: 20, t: 10, b: 20 },
                        xaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)', type: 'date' },
                        yaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)', tickprefix: '₹' },
                        legend: { orientation: 'h', y: 1.15, x: 0.5, xanchor: 'center', font: {size: 10} },
                        hovermode: 'x unified',
                        hoverlabel: { bgcolor: '#161b22', font: { color: '#c9d1d9' }, bordercolor: '#30363d' },
                        shapes: [
                            {
                                type: 'line',
                                x0: todayDate,
                                x1: todayDate,
                                y0: 0,
                                y1: 1,
                                yref: 'paper',
                                line: {
                                    color: '#ff5252',
                                    width: 1.5,
                                    dash: 'dot'
                                }
                            }
                        ],
                        annotations: [
                            {
                                x: todayDate,
                                y: 1,
                                yref: 'paper',
                                text: 'TODAY',
                                showarrow: false,
                                font: { size: 10, color: '#ff5252' },
                                xanchor: 'right',
                                xshift: -5
                            }
                        ]
                    };
                    
                    document.getElementById('forecast-chart').innerHTML = '';
                    // Note: Order matters for tonexty.
                    Plotly.newPlot('forecast-chart', [histTrace, worstTrace, bestTrace, q25Trace, q75Trace, expTrace, aiTrace], layout, {responsive: true});
                    
                    document.getElementById('fc-best').innerText = `₹${best[best.length-1].toFixed(2)}`;
                    document.getElementById('fc-trend').innerText = `₹${ai_trend[ai_trend.length-1].toFixed(2)}`;
                    document.getElementById('fc-worst').innerText = `₹${worst[worst.length-1].toFixed(2)}`;
                } else {
                    if (p) p.innerText = 'Error generating forecast.';
                }
            } catch(e) {
                console.error(e);
                if (p) p.innerText = 'Network error while fetching forecast.';
            } finally {
                forecastBtn.disabled = false;
                forecastBtn.style.opacity = '1';
            }
        });
    }
});


// News Logic
document.addEventListener('DOMContentLoaded', () => {
    const newsBtn = document.getElementById('fetch-news-btn');
    if (newsBtn) {
        newsBtn.addEventListener('click', async () => {
            const selectedTicker = document.getElementById("stock-selector").value || 'RELIANCE';
            const apiTicker = selectedTicker.replace('.NS', '');
            
            const container = document.getElementById('news-feed-container');
            if (container) container.innerHTML = '<p class="placeholder-text" style="text-align: center; padding: 40px; color: #8b949e;"><i class="fa-solid fa-spinner fa-spin"></i> Fetching latest news and calculating VADER sentiment...</p>';
            
            newsBtn.disabled = true;
            newsBtn.style.opacity = '0.5';
            
            try {
                // Fetch Correlation Chart Data
                const corrChart = document.getElementById('sentiment-correlation-chart');
                if (corrChart) corrChart.innerHTML = '<p class="placeholder-text" style="text-align: center; margin-top: 150px; color: #8b949e;"><i class="fa-solid fa-spinner fa-spin"></i> Generating correlation model...</p>';
                
                fetch(`/api/news/correlation/${apiTicker}`).then(r => r.json()).then(corrData => {
                    if (corrData && corrData.dates && corrChart) {
                        const tracePrice = {
                            x: corrData.dates,
                            y: corrData.prices,
                            type: 'scatter',
                            mode: 'lines',
                            name: 'Stock Price',
                            line: { color: '#00b852', width: 2 },
                            yaxis: 'y1'
                        };
                        
                        const traceSentiment = {
                            x: corrData.dates,
                            y: corrData.sentiment,
                            type: 'bar',
                            name: 'News Sentiment',
                            marker: {
                                color: corrData.sentiment.map(s => s > 0 ? 'rgba(0, 184, 82, 0.3)' : (s < 0 ? 'rgba(255, 82, 82, 0.3)' : 'rgba(139, 148, 158, 0.1)')),
                                line: {
                                    color: corrData.sentiment.map(s => s > 0 ? 'rgba(0, 184, 82, 0.8)' : (s < 0 ? 'rgba(255, 82, 82, 0.8)' : 'rgba(139, 148, 158, 0.3)')),
                                    width: 1
                                }
                            },
                            yaxis: 'y2'
                        };
                        
                        const layout = {
                            paper_bgcolor: 'transparent',
                            plot_bgcolor: 'transparent',
                            font: { color: '#c9d1d9' },
                            margin: { t: 20, r: 50, l: 50, b: 40 },
                            xaxis: { showgrid: false, color: '#8b949e' },
                            yaxis: { 
                                title: 'Price (₹)',
                                showgrid: true, 
                                gridcolor: '#30363d', 
                                color: '#00b852' 
                            },
                            yaxis2: {
                                title: 'Sentiment Score',
                                overlaying: 'y',
                                side: 'right',
                                showgrid: false,
                                color: '#8b949e',
                                range: [-1, 1]
                            },
                            legend: { orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' },
                            hovermode: 'x unified'
                        };
                        
                        Plotly.newPlot('sentiment-correlation-chart', [traceSentiment, tracePrice], layout, {responsive: true, displayModeBar: false});
                    }
                }).catch(e => console.error("Correlation fetch error:", e));

                const res = await fetch(`/api/news/${apiTicker}`);
                if (res.ok) {
                    const data = await res.json();
                    const news = data.news || [];
                    
                    if (data.ai_summary && data.ai_summary.length > 0) {
                        const aiCard = document.getElementById('ai-summary-card');
                        const aiList = document.getElementById('ai-summary-list');
                        if (aiCard && aiList) {
                            aiCard.style.display = 'block';
                            aiList.innerHTML = data.ai_summary.map(b => `<li style="margin-bottom: 8px;">${b}</li>`).join('');
                        }
                    }
                    
                    if (news.length === 0) {
                        container.innerHTML = '<p class="placeholder-text" style="text-align: center; padding: 40px; color: #8b949e;">No recent news found for this ticker.</p>';
                        document.getElementById('news-avg-sentiment').innerText = '--';
                        document.getElementById('news-sentiment-label').innerText = '--';
                        return;
                    }
                    
                    let totalScore = 0;
                    let validCount = 0;
                    let html = '';
                    
                    news.forEach(item => {
                        const score = parseFloat(item.Sentiment_Score);
                        if (!isNaN(score)) {
                            totalScore += score;
                            validCount++;
                        }
                        
                        let badgeColor = '#8b949e';
                        if (item.Sentiment_Label.toLowerCase() === 'positive') badgeColor = '#00b852';
                        else if (item.Sentiment_Label.toLowerCase() === 'negative') badgeColor = '#ff5252';
                        
                        html += `
                        <div style="padding: 15px; border: 1px solid #30363d; border-radius: 8px; background: #0d1117;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="font-size: 0.85rem; color: #8b949e;">${item.Source} | ${item['Published At']}</span>
                                <span style="padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; background: ${badgeColor}33; color: ${badgeColor}; border: 1px solid ${badgeColor};">${item.Sentiment_Label}</span>
                            </div>
                            <div style="font-size: 1rem; color: #c9d1d9;">${item.Title}</div>
                        </div>
                        `;
                    });
                    
                    container.innerHTML = html;
                    
                    if (validCount > 0) {
                        const avg = totalScore / validCount;
                        const avgEl = document.getElementById('news-avg-sentiment');
                        const lblEl = document.getElementById('news-sentiment-label');
                        
                        avgEl.innerText = (avg > 0 ? '+' : '') + avg.toFixed(2);
                        if (avg > 0.05) { avgEl.style.color = '#00b852'; lblEl.innerText = 'Bullish'; lblEl.style.color = '#00b852'; }
                        else if (avg < -0.05) { avgEl.style.color = '#ff5252'; lblEl.innerText = 'Bearish'; lblEl.style.color = '#ff5252'; }
                        else { avgEl.style.color = '#8b949e'; lblEl.innerText = 'Neutral'; lblEl.style.color = '#8b949e'; }
                    }
                    

                } else {
                    if (container) container.innerHTML = '<p style="color: #ff5252; text-align: center;">Error fetching news.</p>';
                }
            } catch(e) {
                console.error(e);
                if (container) container.innerHTML = '<p style="color: #ff5252; text-align: center;">Network error while fetching news.</p>';
            } finally {
                newsBtn.disabled = false;
                newsBtn.style.opacity = '1';
            }
        });
    }
});


// Backtest Logic
document.addEventListener('DOMContentLoaded', () => {
    const btBtn = document.getElementById('run-backtest-btn');
    if (btBtn) {
        btBtn.addEventListener('click', async () => {
            const selectedTicker = document.getElementById("stock-selector").value || 'RELIANCE';
            const apiTicker = selectedTicker.replace('.NS', '');
            
            const p = document.getElementById('backtest-placeholder');
            if (p) p.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running historical AI simulation...';
            btBtn.disabled = true;
            btBtn.style.opacity = '0.5';
            
            try {
                const res = await fetch(`/api/backtest/${apiTicker}`);
                if (res.ok) {
                    const data = await res.json();
                    const curve = data.curve;
                    const metrics = data.metrics;
                    
                    // Parse Curve Data
                    const dates = curve.map(c => c.Date);
                    // Standardize start value to ₹100,000 for Indian market
                    const initialEq = curve[0].Strategy_Equity;
                    const multiplier = 100000 / initialEq;
                    
                    const stratEq = curve.map(c => c.Strategy_Equity * multiplier);
                    const bhEq = curve.map(c => c.Buy_Hold_Equity * multiplier);
                    
                    // Traces
                    const stratTrace = {
                        x: dates, y: stratEq,
                        type: 'scatter', mode: 'lines',
                        name: 'AI Strategy',
                        line: { color: '#00e676', width: 3 }
                    };
                    const bhTrace = {
                        x: dates, y: bhEq,
                        type: 'scatter', mode: 'lines',
                        name: 'Buy & Hold',
                        line: { color: '#8b949e', width: 2, dash: 'dot' }
                    };
                    
                    const layout = {
                        paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: '#8b949e', family: 'Inter, sans-serif' },
                        margin: { l: 60, r: 20, t: 10, b: 40 },
                        xaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)' },
                        yaxis: { gridcolor: 'rgba(48, 54, 61, 0.4)', zerolinecolor: 'rgba(48, 54, 61, 0.4)', tickprefix: '₹' },
                        hovermode: 'x unified',
                        legend: { orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' }
                    };
                    
                    document.getElementById('backtest-chart').innerHTML = '';
                    Plotly.newPlot('backtest-chart', [stratTrace, bhTrace], layout, {responsive: true});
                    
                    // Populate KPIs
                    const sMetrics = metrics.Strategy;
                    const bMetrics = metrics.Buy_Hold;
                    
                    const setKPI = (id, sVal, bVal, isPct = true) => {
                        const el = document.getElementById(id);
                        if (!el) return;
                        const sStr = isPct ? (sVal * 100).toFixed(2) + '%' : sVal.toFixed(2);
                        const bStr = isPct ? (bVal * 100).toFixed(2) + '%' : bVal.toFixed(2);
                        
                        let color = '#fff';
                        if (sVal > 0) color = '#00e676';
                        else if (sVal < 0) color = '#ff5252';
                        
                        el.innerHTML = `<span style="color: ${color}">${sStr}</span> <span style="font-size: 0.9rem; color: #8b949e; font-weight: normal;">(vs ${bStr})</span>`;
                    };
                    
                    setKPI('bt-return', sMetrics['Total Return'], bMetrics['Total Return'], true);
                    setKPI('bt-drawdown', sMetrics['Max Drawdown'], bMetrics['Max Drawdown'], true);
                    setKPI('bt-winrate', sMetrics['Win Rate'], bMetrics['Win Rate'], true);
                    setKPI('bt-sharpe', sMetrics['Sharpe Ratio'], bMetrics['Sharpe Ratio'], false);
                    
                } else {
                    if (p) p.innerText = 'Error running backtest.';
                }
            } catch(e) {
                console.error(e);
                if (p) p.innerText = 'Network error while fetching backtest.';
            } finally {
                btBtn.disabled = false;
                btBtn.style.opacity = '1';
            }
        });
    }


    // ==========================================
    // --- Portfolio Management Section Logic ---
    // ==========================================
    let latestPortfolioData = null;
    let currentSectorViewMode = "dual";
    let cachedSectorData = null;
    let cachedBacktestData = null;
    let currentHorizon = "all";

    let portfolioHoldings = [
        { ticker: "RELIANCE", weight: 30, price: 0 },
        { ticker: "TCS", weight: 25, price: 0 },
        { ticker: "INFY", weight: 25, price: 0 },
        { ticker: "ICICIBANK", weight: 20, price: 0 }
    ];

    const availableNiftyTickers = [
        "ADANIPORTS", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJAJFINSV",
        "BAJFINANCE", "BHARTIARTL", "BPCL", "BRITANNIA", "CIPLA",
        "COALINDIA", "DRREDDY", "EICHERMOT", "GAIL", "GRASIM",
        "HCLTECH", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
        "INDUSINDBK", "INFY", "IOC", "ITC", "JSWSTEEL",
        "KOTAKBANK", "LT", "MARUTI", "NESTLEIND", "NTPC",
        "ONGC", "POWERGRID", "RELIANCE", "SBIN", "SHREECEM",
        "SUNPHARMA", "TATASTEEL", "TCS", "TECHM", "TITAN",
        "ULTRACEMCO", "UPL", "VEDL", "WIPRO", "ZEEL"
    ];

    const formatINR = (val) => {
        if (val === undefined || val === null || isNaN(val)) return "₹0";
        return "₹" + Math.round(val).toLocaleString("en-IN");
    };

    function updateWeightTotalBadge() {
        const inputs = document.querySelectorAll(".holding-weight-input");
        let total = 0;
        inputs.forEach(inp => {
            const v = parseFloat(inp.value) || 0;
            total += v;
        });
        const badge = document.getElementById("weight-total-badge");
        if (badge) {
            badge.innerText = `Total Weight: ${Math.round(total)}%`;
            if (Math.abs(total - 100) < 0.5) {
                badge.style.background = "rgba(0, 230, 118, 0.15)";
                badge.style.color = "#00e676";
                badge.style.borderColor = "#00e676";
            } else {
                badge.style.background = "rgba(255, 145, 0, 0.15)";
                badge.style.color = "#ff9100";
                badge.style.borderColor = "#ff9100";
            }
        }
        return total;
    }

    function renderPortfolioTable(recommendations = null, execution = null) {
        const tbody = document.getElementById("portfolio-holdings-tbody");
        if (!tbody) return;

        let recMap = {};
        if (recommendations && Array.isArray(recommendations)) {
            recommendations.forEach(r => {
                recMap[r.ticker] = r;
            });
        }

        let html = "";
        portfolioHoldings.forEach((h, index) => {
            const rec = recMap[h.ticker];
            const currentPrice = rec ? `₹${rec.current_price.toFixed(2)}` : (h.price ? `₹${h.price.toFixed(2)}` : "--");
            const optWeight = rec ? `${rec.optimal_weight}%` : "--";
            
            // Discrete Shares display
            let sharesDisplay = "--";
            if (rec) {
                sharesDisplay = `<div style="font-size: 0.85rem;"><span style="color:#8b949e;">${rec.current_shares} shs</span> → <span style="color:#00e676; font-weight:bold;">${rec.optimal_shares} shs</span></div>`;
            }

            // Action Badge
            const actionBadge = rec ? `<span style="padding: 3px 8px; border-radius: 6px; font-weight: bold; font-size: 0.78rem; background: ${rec.action_color}22; color: ${rec.action_color}; border: 1px solid ${rec.action_color}; white-space: nowrap;">${rec.action}</span>` : `<span style="color: #8b949e;">--</span>`;
            
            const rebalINR = rec ? (rec.delta_inr >= 0 ? `+${formatINR(rec.delta_inr)}` : `-${formatINR(Math.abs(rec.delta_inr))}`) : "--";
            const rebalColor = rec ? (rec.delta_inr >= 0 ? "#00e676" : "#ff5252") : "#8b949e";
            const expRet = rec ? `${rec.stock_ret}%` : "--";
            const stockVol = rec ? `${rec.stock_vol}%` : "--";

            html += `
                <tr style="border-bottom: 1px solid #21262d;">
                    <td style="padding: 12px 10px; font-weight: 600; color: #fff;">
                        <select class="holding-ticker-select" data-index="${index}" style="background: #161b22; color: #fff; border: 1px solid #30363d; border-radius: 6px; padding: 6px 10px; font-size: 0.9rem; font-weight: 600; outline: none;">
                            ${availableNiftyTickers.map(t => `<option value="${t}" ${t === h.ticker ? "selected" : ""}>${t}</option>`).join("")}
                        </select>
                    </td>
                    <td style="padding: 12px 10px; color: #c9d1d9; font-weight: 500;">${currentPrice}</td>
                    <td style="padding: 12px 10px;">
                        <div style="display: flex; align-items: center; gap: 4px;">
                            <input type="number" class="holding-weight-input" data-index="${index}" value="${h.weight}" min="1" max="100" step="1" style="background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #fff; padding: 6px 8px; width: 65px; font-size: 0.9rem; text-align: right; outline: none;">
                            <span style="color: #8b949e;">%</span>
                        </div>
                    </td>
                    <td style="padding: 12px 10px; font-weight: 600; color: ${rec ? "#00e676" : "#8b949e"};">${optWeight}</td>
                    <td style="padding: 12px 10px;">${sharesDisplay}</td>
                    <td style="padding: 12px 10px;">${actionBadge}</td>
                    <td style="padding: 12px 10px; font-weight: 500; color: ${rebalColor};">${rebalINR}</td>
                    <td style="padding: 12px 10px; color: #58a6ff;">${expRet}</td>
                    <td style="padding: 12px 10px; color: #8b949e;">${stockVol}</td>
                    <td style="padding: 12px 10px; text-align: center;">
                        <button class="remove-holding-btn" data-index="${index}" style="background: transparent; border: none; color: #ff5252; cursor: pointer; font-size: 0.95rem; padding: 4px 8px; border-radius: 4px; transition: background 0.2s;" title="Remove stock">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
        updateWeightTotalBadge();

        if (execution) {
            const cashBadge = document.getElementById("discrete-cash-badge");
            if (cashBadge) {
                cashBadge.style.display = "block";
                cashBadge.innerHTML = `<i class="fa-solid fa-coins" style="margin-right: 4px;"></i> Cash Reserve: <strong>${formatINR(execution.optimal_cash_reserve)}</strong>`;
            }
            const minCapVal = document.getElementById("min-capital-val");
            if (minCapVal) {
                minCapVal.innerText = formatINR(execution.min_basket_capital);
            }
        }

        // Attach event listeners to weight inputs
        document.querySelectorAll(".holding-weight-input").forEach(inp => {
            inp.addEventListener("input", (e) => {
                const idx = parseInt(e.target.getAttribute("data-index"));
                const val = parseFloat(e.target.value) || 0;
                portfolioHoldings[idx].weight = val;
                updateWeightTotalBadge();
            });
        });

        // Attach event listeners to ticker dropdowns
        document.querySelectorAll(".holding-ticker-select").forEach(sel => {
            sel.addEventListener("change", (e) => {
                const idx = parseInt(e.target.getAttribute("data-index"));
                portfolioHoldings[idx].ticker = e.target.value;
            });
        });

        // Attach event listeners to remove buttons
        document.querySelectorAll(".remove-holding-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const idx = parseInt(btn.getAttribute("data-index"));
                if (portfolioHoldings.length <= 2) {
                    alert("A diversified portfolio requires at least 2 stocks.");
                    return;
                }
                portfolioHoldings.splice(idx, 1);
                // Redistribute weights proportionally
                let total = portfolioHoldings.reduce((sum, h) => sum + h.weight, 0);
                if (total > 0) {
                    portfolioHoldings.forEach(h => h.weight = Math.round((h.weight / total) * 100));
                }
                renderPortfolioTable(recommendations, execution);
            });
        });
    }

    // Add Stock button
    const addHoldingBtn = document.getElementById("add-holding-btn");
    if (addHoldingBtn) {
        addHoldingBtn.addEventListener("click", () => {
            const currentTickers = portfolioHoldings.map(h => h.ticker);
            const nextTicker = availableNiftyTickers.find(t => !currentTickers.includes(t)) || "SBIN";
            portfolioHoldings.push({ ticker: nextTicker, weight: 10, price: 0 });
            // Re-normalize weights
            let total = portfolioHoldings.reduce((sum, h) => sum + h.weight, 0);
            portfolioHoldings.forEach(h => h.weight = Math.round((h.weight / total) * 100));
            renderPortfolioTable();
        });
    }

    // Reset Bluechips button
    const resetPortfolioBtn = document.getElementById("reset-portfolio-btn");
    if (resetPortfolioBtn) {
        resetPortfolioBtn.addEventListener("click", () => {
            portfolioHoldings = [
                { ticker: "RELIANCE", weight: 30, price: 0 },
                { ticker: "TCS", weight: 25, price: 0 },
                { ticker: "INFY", weight: 25, price: 0 },
                { ticker: "ICICIBANK", weight: 20, price: 0 }
            ];
            const warningBanner = document.getElementById("portfolio-warning-banner");
            if (warningBanner) warningBanner.style.display = "none";
            renderPortfolioTable();
        });
    }

    // Run AI Optimization Button
    const runPortfolioBtn = document.getElementById("run-portfolio-btn");
    if (runPortfolioBtn) {
        runPortfolioBtn.addEventListener("click", async () => {
            const warningBanner = document.getElementById("portfolio-warning-banner");
            const warningText = document.getElementById("portfolio-warning-text");
            if (warningBanner) warningBanner.style.display = "none";

            const capitalInput = document.getElementById("portfolio-capital-input");
            const capital = parseFloat(capitalInput ? capitalInput.value : 1000000) || 0;

            if (capital < 500) {
                if (warningBanner && warningText) {
                    warningBanner.style.display = "flex";
                    warningText.innerHTML = `<strong>Insufficient Capital:</strong> In Indian stock markets (NSE/BSE), fractional shares are not supported. With ₹${capital.toFixed(2)}, you cannot purchase even a single share of stocks like INFY (₹1,035) or ICICIBANK (₹1,310). Please enter at least ₹5,000+ to allocate whole shares.`;
                }
                return;
            }

            runPortfolioBtn.disabled = true;
            runPortfolioBtn.style.opacity = "0.6";
            runPortfolioBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="margin-right: 8px;"></i> Optimizing Frontier...`;

            try {
                // Ensure weights are synchronized
                document.querySelectorAll(".holding-weight-input").forEach(inp => {
                    const idx = parseInt(inp.getAttribute("data-index"));
                    portfolioHoldings[idx].weight = parseFloat(inp.value) || 0;
                });

                const payload = {
                    initial_investment: capital,
                    risk_free_rate: 0.065,
                    holdings: portfolioHoldings.map(h => ({ ticker: h.ticker, weight: h.weight }))
                };

                const res = await fetch("/api/portfolio/analyze", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || "Optimization failed");
                }

                const data = await res.json();
                latestPortfolioData = data;

                // Show "Apply AI Weights" button
                const btnApply = document.getElementById("btn-apply-rebalance");
                if (btnApply) btnApply.style.display = "inline-flex";

                // 1. Update Top KPIs
                const cMet = data.metrics.current;
                const oMet = data.metrics.optimal;

                document.getElementById("port-kpi-return").innerText = `${cMet.expected_return_pct}%`;
                const retDiff = (oMet.expected_return_pct - cMet.expected_return_pct).toFixed(2);
                document.getElementById("port-kpi-return-delta").innerHTML = `AI Optimal: <span style="color: #00e676; font-weight: bold;">${oMet.expected_return_pct}%</span> (+${retDiff}%)`;

                document.getElementById("port-kpi-risk").innerText = `${cMet.volatility_pct}%`;
                const riskDiff = (oMet.volatility_pct - cMet.volatility_pct).toFixed(2);
                const riskDiffColor = riskDiff <= 0 ? "#00e676" : "#ff5252";
                document.getElementById("port-kpi-risk-delta").innerHTML = `AI Optimal: <span style="color: ${riskDiffColor}; font-weight: bold;">${oMet.volatility_pct}%</span> (${riskDiff}%)`;

                document.getElementById("port-kpi-sharpe").innerText = cMet.sharpe_ratio.toFixed(2);
                const sharpeDiff = (oMet.sharpe_ratio - cMet.sharpe_ratio).toFixed(2);
                document.getElementById("port-kpi-sharpe-delta").innerHTML = `AI Optimal: <span style="color: #00e676; font-weight: bold;">${oMet.sharpe_ratio.toFixed(2)}</span> (+${sharpeDiff})`;

                document.getElementById("port-kpi-beta").innerText = cMet.beta.toFixed(2);

                const alphaBadge = document.getElementById("rebalance-alpha-badge");
                if (alphaBadge) {
                    alphaBadge.style.display = "block";
                    alphaBadge.innerText = `Projected AI Alpha: +${formatINR(oMet.projected_alpha_inr)} (+${oMet.alpha_pct.toFixed(1)}%)`;
                }
                const kpiAlpha = document.getElementById("port-kpi-alpha");
                if (kpiAlpha) kpiAlpha.innerText = `+${formatINR(oMet.projected_alpha_inr)}`;
                const kpiAlphaPct = document.getElementById("port-kpi-alpha-pct");
                if (kpiAlphaPct) kpiAlphaPct.innerText = `+${oMet.alpha_pct.toFixed(1)}% vs. Unbalanced`;

                // 2. Re-render table with recommendations and discrete execution info
                renderPortfolioTable(data.rebalance_recommendations, data.discrete_execution);

                // 2b. Render Actionable Execution Order Sheet
                renderExecutionOrderSheet(data.order_sheet);

                // 2c. Render Sector & Industry Exposure Breakdown (Institutional 25% Limits)
                renderSectorExposure(data.sector_exposure);

                // 2d. Render Historical Backtest of Rebalanced Portfolio (Equity Curve)
                renderHistoricalBacktest(data.historical_backtest);

                // 3. Render Markowitz Efficient Frontier Plotly Chart
                const frontierCloud = data.efficient_frontier.cloud;
                const curPt = data.efficient_frontier.current_point;
                const optPt = data.efficient_frontier.optimal_point;
                const minPt = data.efficient_frontier.min_vol_point;

                const cloudTrace = {
                    x: frontierCloud.map(p => p.vol),
                    y: frontierCloud.map(p => p.ret),
                    mode: "markers",
                    type: "scatter",
                    name: "Simulated Portfolios",
                    marker: {
                        size: 4.5,
                        color: frontierCloud.map(p => p.sharpe),
                        colorscale: [
                            [0, "rgba(33, 150, 243, 0.4)"],
                            [0.5, "rgba(0, 230, 118, 0.7)"],
                            [1, "rgba(255, 235, 59, 1.0)"]
                        ],
                        colorbar: {
                            title: { text: "Sharpe", font: { color: "#8b949e", size: 10 } },
                            tickfont: { color: "#8b949e", size: 9 },
                            thickness: 12,
                            len: 0.8
                        },
                        opacity: 0.65
                    },
                    hovertemplate: "<b>Volatility:</b> %{x}%<br><b>Expected Return:</b> %{y}%<br><b>Sharpe:</b> %{marker.color:.2f}<extra></extra>"
                };

                const currentTrace = {
                    x: [curPt.vol],
                    y: [curPt.ret],
                    mode: "markers+text",
                    type: "scatter",
                    name: "Current Portfolio",
                    text: ["Current"],
                    textposition: "top left",
                    textfont: { color: "#ffffff", size: 11, family: "Inter, sans-serif" },
                    marker: { size: 13, color: "#ffffff", symbol: "circle", line: { color: "#3399ff", width: 2.5 } },
                    hovertemplate: "<b>Current Portfolio</b><br>Vol: %{x}%<br>Return: %{y}%<br>Sharpe: " + curPt.sharpe + "<extra></extra>"
                };

                const optimalTrace = {
                    x: [optPt.vol],
                    y: [optPt.ret],
                    mode: "markers+text",
                    type: "scatter",
                    name: "AI Optimal (Max Sharpe)",
                    text: ["★ Max Sharpe"],
                    textposition: "top right",
                    textfont: { color: "#00e676", size: 12, weight: "bold", family: "Inter, sans-serif" },
                    marker: { size: 16, color: "#00e676", symbol: "star", line: { color: "#ffffff", width: 1.5 } },
                    hovertemplate: "<b>AI Optimal Tangency</b><br>Vol: %{x}%<br>Return: %{y}%<br>Sharpe: " + optPt.sharpe + "<extra></extra>"
                };

                const minVolTrace = {
                    x: [minPt.vol],
                    y: [minPt.ret],
                    mode: "markers+text",
                    type: "scatter",
                    name: "Min Volatility",
                    text: ["Min Risk"],
                    textposition: "bottom right",
                    textfont: { color: "#3399ff", size: 10, family: "Inter, sans-serif" },
                    marker: { size: 12, color: "#3399ff", symbol: "diamond" },
                    hovertemplate: "<b>Minimum Volatility</b><br>Vol: %{x}%<br>Return: %{y}%<br>Sharpe: " + minPt.sharpe + "<extra></extra>"
                };

                const frontierLayout = {
                    paper_bgcolor: "rgba(0,0,0,0)",
                    plot_bgcolor: "rgba(0,0,0,0)",
                    font: { color: "#8b949e", family: "Inter, sans-serif" },
                    margin: { l: 55, r: 20, t: 20, b: 45 },
                    xaxis: {
                        title: { text: "Annualized Volatility / Risk (%)", font: { size: 11, color: "#8b949e" } },
                        gridcolor: "rgba(48, 54, 61, 0.4)",
                        zerolinecolor: "rgba(48, 54, 61, 0.4)"
                    },
                    yaxis: {
                        title: { text: "Annualized Expected Return (%)", font: { size: 11, color: "#8b949e" } },
                        gridcolor: "rgba(48, 54, 61, 0.4)",
                        zerolinecolor: "rgba(48, 54, 61, 0.4)"
                    },
                    legend: { orientation: "h", y: 1.15, x: 0.5, xanchor: "center", font: { size: 10 } },
                    hovermode: "closest"
                };

                document.getElementById("efficient-frontier-chart").innerHTML = "";
                Plotly.newPlot("efficient-frontier-chart", [cloudTrace, currentTrace, minVolTrace, optimalTrace], frontierLayout, { responsive: true });

                // 4. Render Allocation Comparison Chart (Grouped Horizontal Bars)
                const recs = data.rebalance_recommendations;
                const tickersList = recs.map(r => r.ticker).reverse();
                const curWeights = recs.map(r => r.current_weight).reverse();
                const optWeights = recs.map(r => r.optimal_weight).reverse();

                const barCur = {
                    y: tickersList,
                    x: curWeights,
                    name: "Current (%)",
                    type: "bar",
                    orientation: "h",
                    marker: { color: "#3399ff" }
                };

                const barOpt = {
                    y: tickersList,
                    x: optWeights,
                    name: "AI Recommended (%)",
                    type: "bar",
                    orientation: "h",
                    marker: { color: "#00e676" }
                };

                const barLayout = {
                    paper_bgcolor: "rgba(0,0,0,0)",
                    plot_bgcolor: "rgba(0,0,0,0)",
                    font: { color: "#8b949e", family: "Inter, sans-serif" },
                    margin: { l: 85, r: 20, t: 20, b: 40 },
                    barmode: "group",
                    bargap: 0.25,
                    bargroupgap: 0.1,
                    xaxis: {
                        title: { text: "Allocation Weight (%)", font: { size: 11, color: "#8b949e" } },
                        gridcolor: "rgba(48, 54, 61, 0.4)",
                        zerolinecolor: "rgba(48, 54, 61, 0.4)"
                    },
                    yaxis: {
                        tickfont: { color: "#fff", size: 11 }
                    },
                    legend: { orientation: "h", y: 1.15, x: 0.5, xanchor: "center", font: { size: 10 } }
                };

                document.getElementById("allocation-comparison-chart").innerHTML = "";
                Plotly.newPlot("allocation-comparison-chart", [barCur, barOpt], barLayout, { responsive: true });

                // 4b. Render Asset Correlation Heatmap and AI Insights
                const corrData = data.correlation;
                const insightsContainer = document.getElementById("portfolio-correlation-insights");
                if (insightsContainer && corrData && corrData.insights) {
                    insightsContainer.innerHTML = corrData.insights.map(ins => {
                        const isWarn = ins.type === "warning";
                        const bg = isWarn ? "rgba(255, 82, 82, 0.12)" : "rgba(0, 230, 118, 0.12)";
                        const border = isWarn ? "#ff5252" : "#00e676";
                        const icon = isWarn ? "fa-triangle-exclamation" : "fa-shield-halved";
                        return `
                            <div style="padding: 10px 14px; border-radius: 8px; background: ${bg}; border-left: 4px solid ${border}; display: flex; align-items: flex-start; gap: 10px; font-size: 0.88rem; color: #c9d1d9;">
                                <i class="fa-solid ${icon}" style="color: ${border}; margin-top: 3px;"></i>
                                <div style="flex: 1;">
                                    <span style="font-weight: 700; color: #fff;">${ins.pair}:</span> ${ins.message}
                                </div>
                            </div>
                        `;
                    }).join("");
                }

                if (corrData && corrData.matrix && corrData.tickers) {
                    const zValues = corrData.matrix;
                    const xLabels = corrData.tickers;
                    const yLabels = corrData.tickers;

                    // Annotations for exact numbers inside heatmap cells
                    const annotations = [];
                    for (let i = 0; i < yLabels.length; i++) {
                        for (let j = 0; j < xLabels.length; j++) {
                            const val = zValues[i][j];
                            annotations.push({
                                xref: "x1",
                                yref: "y1",
                                x: xLabels[j],
                                y: yLabels[i],
                                text: val.toFixed(2),
                                font: {
                                    family: "Inter, sans-serif",
                                    size: 13,
                                    color: "#ffffff"
                                },
                                showarrow: false
                            });
                        }
                    }

                    const corrHeatmapTrace = {
                        z: zValues,
                        x: xLabels,
                        y: yLabels,
                        type: "heatmap",
                        colorscale: [
                            [0, "#00e676"],      // Low correlation (green = great diversification)
                            [0.4, "#3399ff"],    // Moderate correlation (blue)
                            [0.7, "#ff9100"],    // Higher correlation (orange)
                            [1.0, "#ff5252"]     // High correlation (red = concentration risk)
                        ],
                        zmin: -0.2,
                        zmax: 1.0,
                        hoverongaps: false,
                        hovertemplate: "<b>%{y} vs %{x}</b><br>Correlation: %{z:.2f}<extra></extra>",
                        colorbar: {
                            title: { text: "Correlation", font: { color: "#8b949e", size: 10 } },
                            tickfont: { color: "#8b949e", size: 9 },
                            thickness: 12,
                            len: 0.85
                        }
                    };

                    const corrLayout = {
                        paper_bgcolor: "rgba(0,0,0,0)",
                        plot_bgcolor: "rgba(0,0,0,0)",
                        font: { color: "#8b949e", family: "Inter, sans-serif" },
                        margin: { l: 85, r: 20, t: 20, b: 60 },
                        xaxis: {
                            tickfont: { color: "#fff", size: 11 },
                            gridcolor: "transparent"
                        },
                        yaxis: {
                            tickfont: { color: "#fff", size: 11 },
                            gridcolor: "transparent"
                        },
                        annotations: annotations
                    };

                    document.getElementById("portfolio-correlation-chart").innerHTML = "";
                    Plotly.newPlot("portfolio-correlation-chart", [corrHeatmapTrace], corrLayout, { responsive: true });
                }

                // 4c. Render Black Swan Simulator & Historical Stress Testing
                const stressData = data.stress_testing;
                if (stressData) {
                    // Update VaR Risk Gauge Cards
                    const varCur = stressData.var_metrics.current;
                    const varOpt = stressData.var_metrics.optimal;

                    const elVar1d = document.getElementById("var-1d-val");
                    if (elVar1d) elVar1d.innerHTML = `-${varCur.var_1d_pct}% <span style="font-size:0.85rem; font-weight:normal; color:#8b949e;">(-${formatINR(varCur.var_1d_inr)})</span>`;

                    const elVar1m = document.getElementById("var-1m-val");
                    if (elVar1m) elVar1m.innerHTML = `-${varCur.var_1m_pct}% <span style="font-size:0.85rem; font-weight:normal; color:#8b949e;">(-${formatINR(varCur.var_1m_inr)})</span>`;

                    const elCvar = document.getElementById("cvar-val");
                    if (elCvar) elCvar.innerHTML = `-${varCur.cvar_pct}% <span style="font-size:0.85rem; font-weight:normal; color:#8b949e;">(-${formatINR(varCur.cvar_inr)})</span>`;

                    // AI Tail Risk Cushion (Risk reduction in Rupees)
                    const var1mSavings = varCur.var_1m_inr - varOpt.var_1m_inr;
                    const elCushion = document.getElementById("ai-var-cushion-val");
                    if (elCushion) {
                        if (var1mSavings >= 0) {
                            elCushion.innerHTML = `+${formatINR(var1mSavings)} <span style="font-size:0.85rem; font-weight:normal; color:#00e676;">Saved</span>`;
                        } else {
                            elCushion.innerHTML = `${formatINR(Math.abs(var1mSavings))} <span style="font-size:0.85rem; font-weight:normal; color:#8b949e;">Active</span>`;
                        }
                    }

                    // Render Scenario Cards
                    const scenarios = stressData.scenarios;
                    const scenarioCardsContainer = document.getElementById("stress-scenario-cards-container");
                    if (scenarioCardsContainer && scenarios) {
                        scenarioCardsContainer.innerHTML = scenarios.map(sc => {
                            const isSaved = sc.capital_saved_inr > 0;
                            const isSteeper = sc.capital_saved_inr < 0;

                            let savedBadge = "";
                            let optDropColor = "#a371f7";
                            if (isSaved) {
                                savedBadge = `<span style="padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; background: rgba(0, 230, 118, 0.15); color: #00e676; border: 1px solid #00e676;"><i class="fa-solid fa-shield-halved" style="margin-right: 4px;"></i>+${formatINR(sc.capital_saved_inr)} Protected</span>`;
                                optDropColor = "#00e676";
                            } else if (isSteeper) {
                                savedBadge = `<span style="padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; background: rgba(227, 179, 65, 0.15); color: #e3b341; border: 1px solid #e3b341;"><i class="fa-solid fa-bolt" style="margin-right: 4px;"></i>Cyclical Growth Tilt</span>`;
                                optDropColor = "#e3b341";
                            } else {
                                savedBadge = `<span style="padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; background: rgba(88, 166, 255, 0.15); color: #58a6ff; border: 1px solid #58a6ff;">Risk Parity</span>`;
                                optDropColor = "#58a6ff";
                            }

                            return `
                                <div style="background: #0d1117; border: 1px solid #30363d; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between;">
                                    <div>
                                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                                            <h4 style="color: #fff; font-size: 0.95rem; font-weight: 600;">${sc.name}</h4>
                                            ${savedBadge}
                                        </div>
                                        <div style="font-size: 0.75rem; color: #8b949e; margin-bottom: 10px;">
                                            Benchmark: <strong style="color: #ff5252;">${sc.benchmark_drop_pct}%</strong> | ${sc.period}
                                        </div>
                                        <p style="font-size: 0.8rem; color: #8b949e; margin-bottom: 14px; line-height: 1.4;">
                                            ${sc.description}
                                        </p>
                                    </div>

                                    <div style="background: #161b22; border: 1px solid #21262d; border-radius: 6px; padding: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8rem;">
                                        <div>
                                            <div style="color: #8b949e; font-size: 0.72rem;">Current Drawdown</div>
                                            <div style="color: #58a6ff; font-weight: bold; font-size: 0.9rem;">${sc.current_drawdown_pct}%</div>
                                            <div style="color: #8b949e; font-size: 0.72rem;">-${formatINR(sc.current_loss_inr)}</div>
                                        </div>
                                        <div>
                                            <div style="color: #8b949e; font-size: 0.72rem;">AI Optimal Drawdown</div>
                                            <div style="color: ${optDropColor}; font-weight: bold; font-size: 0.9rem;">${sc.optimal_drawdown_pct}%</div>
                                            <div style="color: #8b949e; font-size: 0.72rem;">-${formatINR(sc.optimal_loss_inr)}</div>
                                        </div>
                                        <div style="grid-column: span 2; border-top: 1px solid #30363d; padding-top: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem;">
                                            <span style="color: #8b949e;">Est. Recovery Duration:</span>
                                            <span style="color: #fff; font-weight: 600;"><i class="fa-solid fa-clock-rotate-left" style="color: #58a6ff; margin-right: 4px;"></i> ~${sc.recovery_days_opt} trading days</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join("");
                    }

                    // Render Plotly Comparative Drawdown Bar Chart
                    const chartNames = scenarios.map(s => s.name);
                    const curDrops = scenarios.map(s => s.current_drawdown_pct);
                    const optDrops = scenarios.map(s => s.optimal_drawdown_pct);

                    const traceCurBar = {
                        x: chartNames,
                        y: curDrops,
                        name: "Current Allocation",
                        type: "bar",
                        marker: { 
                            color: "#388bfd",
                            line: { color: "#58a6ff", width: 1 }
                        },
                        text: curDrops.map(v => `${v}%`),
                        textposition: "inside",
                        insidetextanchor: "middle",
                        textfont: { color: "#ffffff", size: 11, family: "Inter, sans-serif" }
                    };

                    const traceOptBar = {
                        x: chartNames,
                        y: optDrops,
                        name: "AI Optimal Allocation",
                        type: "bar",
                        marker: { 
                            color: "#a371f7",
                            line: { color: "#bc8cff", width: 1 }
                        },
                        text: optDrops.map(v => `${v}%`),
                        textposition: "inside",
                        insidetextanchor: "middle",
                        textfont: { color: "#ffffff", size: 11, family: "Inter, sans-serif" }
                    };

                    // Dynamic Y-axis lower bound to prevent any text clipping or label collisions
                    const allDrops = [...curDrops, ...optDrops];
                    const minDropVal = allDrops.length > 0 ? Math.min(...allDrops) : -70;
                    const yAxisMin = Math.floor((minDropVal - 15) / 10) * 10;

                    const stressLayout = {
                        paper_bgcolor: "rgba(0,0,0,0)",
                        plot_bgcolor: "rgba(0,0,0,0)",
                        font: { color: "#8b949e", family: "Inter, sans-serif" },
                        margin: { l: 55, r: 20, t: 30, b: 65 },
                        barmode: "group",
                        bargap: 0.28,
                        bargroupgap: 0.12,
                        yaxis: {
                            title: { text: "Peak-to-Trough Drawdown (%)", font: { size: 11, color: "#8b949e" } },
                            gridcolor: "rgba(48, 54, 61, 0.4)",
                            zerolinecolor: "rgba(48, 54, 61, 0.7)",
                            zerolinewidth: 1.5,
                            ticksuffix: "%",
                            range: [yAxisMin, 5]
                        },
                        xaxis: {
                            tickfont: { color: "#c9d1d9", size: 11 },
                            tickangle: 0
                        },
                        legend: { 
                            orientation: "h", 
                            y: 1.15, 
                            x: 0.5, 
                            xanchor: "center", 
                            font: { size: 11, color: "#c9d1d9" } 
                        }
                    };

                    document.getElementById("portfolio-stress-chart").innerHTML = "";
                    Plotly.newPlot("portfolio-stress-chart", [traceCurBar, traceOptBar], stressLayout, { responsive: true });
                }

                // 5. Render 1-Year Net Worth Monte Carlo Simulation
                const simData = data.net_worth_simulation;
                const simDates = simData.dates;
                const cExp = simData.current.expected;
                const cWorst = simData.current.worst;
                const cBest = simData.current.best;

                const oExp = simData.optimal.expected;
                const oQ25 = simData.optimal.q25;
                const oQ75 = simData.optimal.q75;
                const oWorst = simData.optimal.worst;
                const oBest = simData.optimal.best;

                // Optimal Shaded Bands
                const traceOptWorst = {
                    x: simDates, y: oWorst,
                    type: "scatter", mode: "lines",
                    name: "AI 5th Percentile",
                    line: { color: "#00e676", width: 0 },
                    showlegend: false
                };
                const traceOptBest = {
                    x: simDates, y: oBest,
                    type: "scatter", mode: "lines",
                    name: "AI 90% Confidence (Outer)",
                    line: { color: "#00e676", width: 0 },
                    fill: "tonexty",
                    fillcolor: "rgba(0, 230, 118, 0.08)"
                };
                const traceOptQ25 = {
                    x: simDates, y: oQ25,
                    type: "scatter", mode: "lines",
                    name: "AI 25th Percentile",
                    line: { color: "#00e676", width: 0 },
                    showlegend: false
                };
                const traceOptQ75 = {
                    x: simDates, y: oQ75,
                    type: "scatter", mode: "lines",
                    name: "AI 50% Confidence (Inner)",
                    line: { color: "#00e676", width: 0 },
                    fill: "tonexty",
                    fillcolor: "rgba(0, 230, 118, 0.16)"
                };

                // Optimal Expected Line
                const traceOptExp = {
                    x: simDates, y: oExp,
                    type: "scatter", mode: "lines",
                    name: "AI Rebalanced Expected",
                    line: { color: "#00e676", width: 3 }
                };

                // Current Expected Line
                const traceCurExp = {
                    x: simDates, y: cExp,
                    type: "scatter", mode: "lines",
                    name: "Current Portfolio Expected",
                    line: { color: "#3399ff", width: 2, dash: "dot" }
                };

                // Baseline Starting Capital Line
                const traceBaseline = {
                    x: [simDates[0], simDates[simDates.length - 1]],
                    y: [capital, capital],
                    type: "scatter", mode: "lines",
                    name: "Starting Capital (₹)",
                    line: { color: "#8b949e", width: 1.5, dash: "dash" }
                };

                const simLayout = {
                    paper_bgcolor: "rgba(0,0,0,0)",
                    plot_bgcolor: "rgba(0,0,0,0)",
                    font: { color: "#8b949e", family: "Inter, sans-serif" },
                    margin: { l: 85, r: 20, t: 15, b: 35 },
                    xaxis: {
                        gridcolor: "rgba(48, 54, 61, 0.4)",
                        zerolinecolor: "rgba(48, 54, 61, 0.4)",
                        type: "date"
                    },
                    yaxis: {
                        gridcolor: "rgba(48, 54, 61, 0.4)",
                        zerolinecolor: "rgba(48, 54, 61, 0.4)",
                        tickprefix: "₹"
                    },
                    legend: { orientation: "h", y: 1.15, x: 0.5, xanchor: "center", font: { size: 10 } },
                    hovermode: "x unified",
                    hoverlabel: { bgcolor: "#161b22", font: { color: "#c9d1d9" }, bordercolor: "#30363d" }
                };

                document.getElementById("portfolio-networth-chart").innerHTML = "";
                Plotly.newPlot("portfolio-networth-chart", [
                    traceBaseline,
                    traceOptWorst, traceOptBest,
                    traceOptQ25, traceOptQ75,
                    traceCurExp,
                    traceOptExp
                ], simLayout, { responsive: true });

            } catch (err) {
                console.error("Portfolio optimization error:", err);
                const warningBanner = document.getElementById("portfolio-warning-banner");
                const warningText = document.getElementById("portfolio-warning-text");
                if (warningBanner && warningText) {
                    warningBanner.style.display = "flex";
                    warningText.innerHTML = `<strong>Validation Error:</strong> ${err.message}`;
                } else {
                    alert("Portfolio Optimization Error: " + err.message);
                }
            } finally {
                runPortfolioBtn.disabled = false;
                runPortfolioBtn.style.opacity = "1";
                runPortfolioBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles" style="margin-right: 8px;"></i> Run AI Optimization`;
            }
        });
    }

    // -------------------------------------------------------------
    // --- 2b. Execution Order Sheet Generator (Actionable Trades) -
    // -------------------------------------------------------------
    function renderExecutionOrderSheet(orderSheet) {
        const container = document.getElementById("portfolio-order-sheet-container");
        if (!container || !orderSheet) return;
        container.style.display = "block";

        const listEl = document.getElementById("portfolio-order-sheet-list");
        const summaryEl = document.getElementById("portfolio-order-sheet-summary");

        let cardsHtml = "";

        // SELL Orders First
        if (orderSheet.sell_orders && orderSheet.sell_orders.length > 0) {
            orderSheet.sell_orders.forEach(ord => {
                cardsHtml += `
                    <div style="background: rgba(255, 82, 82, 0.08); border: 1px solid rgba(255, 82, 82, 0.3); border-radius: 6px; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="background: #ff5252; color: #fff; font-size: 0.72rem; font-weight: bold; padding: 2px 6px; border-radius: 3px;">SELL</span>
                                <span style="color: #fff; font-weight: 600; font-size: 0.92rem;">${ord.ticker}</span>
                            </div>
                            <div style="color: #8b949e; font-size: 0.76rem; margin-top: 4px;">
                                ${ord.shares} shares @ ₹${ord.price.toLocaleString('en-IN')}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: #ff5252; font-weight: bold; font-size: 0.92rem;">+₹${ord.value_inr.toLocaleString('en-IN')}</div>
                            <div style="color: #8b949e; font-size: 0.72rem;">Proceeds</div>
                        </div>
                    </div>
                `;
            });
        }

        // BUY Orders
        if (orderSheet.buy_orders && orderSheet.buy_orders.length > 0) {
            orderSheet.buy_orders.forEach(ord => {
                cardsHtml += `
                    <div style="background: rgba(0, 230, 118, 0.08); border: 1px solid rgba(0, 230, 118, 0.3); border-radius: 6px; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="background: #00e676; color: #0d1117; font-size: 0.72rem; font-weight: bold; padding: 2px 6px; border-radius: 3px;">BUY</span>
                                <span style="color: #fff; font-weight: 600; font-size: 0.92rem;">${ord.ticker}</span>
                            </div>
                            <div style="color: #8b949e; font-size: 0.76rem; margin-top: 4px;">
                                +${ord.shares} shares @ ₹${ord.price.toLocaleString('en-IN')}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: #00e676; font-weight: bold; font-size: 0.92rem;">-₹${ord.value_inr.toLocaleString('en-IN')}</div>
                            <div style="color: #8b949e; font-size: 0.72rem;">Outflow</div>
                        </div>
                    </div>
                `;
            });
        }

        // HOLD Orders
        if (orderSheet.hold_orders && orderSheet.hold_orders.length > 0) {
            orderSheet.hold_orders.forEach(ord => {
                cardsHtml += `
                    <div style="background: rgba(88, 166, 255, 0.06); border: 1px solid rgba(88, 166, 255, 0.2); border-radius: 6px; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="background: #388bfd; color: #fff; font-size: 0.72rem; font-weight: bold; padding: 2px 6px; border-radius: 3px;">HOLD</span>
                                <span style="color: #fff; font-weight: 600; font-size: 0.92rem;">${ord.ticker}</span>
                            </div>
                            <div style="color: #8b949e; font-size: 0.76rem; margin-top: 4px;">
                                Target allocation matched
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: #58a6ff; font-weight: 600; font-size: 0.85rem;">No Trade</div>
                        </div>
                    </div>
                `;
            });
        }

        if (listEl) listEl.innerHTML = cardsHtml;

        // Summary Ribbon
        if (summaryEl) {
            const netFlowSign = orderSheet.net_cash_flow_inr >= 0 ? "+" : "";
            const netFlowColor = orderSheet.net_cash_flow_inr >= 0 ? "#00e676" : "#ff5252";
            summaryEl.innerHTML = `
                <div>
                    <span style="color: #8b949e;">Sell Inflow:</span>
                    <strong style="color: #ff7b72; margin-left: 4px;">+₹${orderSheet.total_sell_val_inr.toLocaleString('en-IN')}</strong>
                </div>
                <div>
                    <span style="color: #8b949e;">Buy Outflow:</span>
                    <strong style="color: #00e676; margin-left: 4px;">-₹${orderSheet.total_buy_val_inr.toLocaleString('en-IN')}</strong>
                </div>
                <div>
                    <span style="color: #8b949e;">Net Rebalance Cash Flow:</span>
                    <strong style="color: ${netFlowColor}; margin-left: 4px;">${netFlowSign}₹${orderSheet.net_cash_flow_inr.toLocaleString('en-IN')}</strong>
                </div>
                <div>
                    <span style="color: #8b949e;">Target Cash Reserve:</span>
                    <strong style="color: #58a6ff; margin-left: 4px;">₹${orderSheet.optimal_cash_reserve.toLocaleString('en-IN')}</strong>
                </div>
            `;
        }

        // Copy to Broker handler
        const copyBtn = document.getElementById("btn-copy-orders");
        if (copyBtn) {
            copyBtn.onclick = () => {
                const rawText = orderSheet.raw_broker_text || "";
                navigator.clipboard.writeText(rawText).then(() => {
                    const btnText = document.getElementById("copy-btn-text");
                    if (btnText) {
                        btnText.innerText = "✓ Orders Copied!";
                        setTimeout(() => { btnText.innerText = "Copy Orders for Broker"; }, 2500);
                    }
                }).catch(() => {
                    alert(rawText);
                });
            };
        }
    }

    // -------------------------------------------------------------
    // --- 2c. Sector & Industry Exposure Breakdown (25% Limits) ---
    // -------------------------------------------------------------
    const sectorColorsMap = {
        "Banking & Financials": "#388bfd",
        "IT & Technology": "#2ebd85",
        "Energy & Power": "#f0883e",
        "Automobile & Components": "#a371f7",
        "Consumer Goods (FMCG)": "#56d364",
        "Pharma & Healthcare": "#ec6547",
        "Metals & Mining": "#79c0ff",
        "Infrastructure & Capital Goods": "#d2a8ff",
        "Telecom & Media": "#ff7b72",
        "Diversified / Other": "#8b949e"
    };

    function renderSectorExposure(sectorData) {
        if (!sectorData) return;
        cachedSectorData = sectorData;

        // Render AI Sector Concentration Alerts
        const insightsContainer = document.getElementById("portfolio-sector-insights");
        if (insightsContainer && sectorData.insights) {
            insightsContainer.innerHTML = sectorData.insights.map(ins => {
                const isWarn = ins.type === "warning";
                const isResolved = ins.type === "warning_resolved";
                const bg = isWarn ? "rgba(255, 82, 82, 0.12)" : isResolved ? "rgba(255, 179, 0, 0.12)" : "rgba(0, 230, 118, 0.12)";
                const border = isWarn ? "#ff5252" : isResolved ? "#e3b341" : "#00e676";
                const icon = isWarn ? "fa-triangle-exclamation" : isResolved ? "fa-circle-check" : "fa-shield-halved";
                return `
                    <div style="padding: 10px 14px; border-radius: 8px; background: ${bg}; border-left: 4px solid ${border}; display: flex; align-items: flex-start; gap: 10px; font-size: 0.88rem; color: #c9d1d9;">
                        <i class="fa-solid ${icon}" style="color: ${border}; margin-top: 3px;"></i>
                        <div style="flex: 1;">${ins.message}</div>
                    </div>
                `;
            }).join("");
        }

        // Render Sector Progress Table
        const tbody = document.getElementById("portfolio-sector-tbody");
        if (tbody && sectorData.sectors) {
            tbody.innerHTML = sectorData.sectors.map(sec => {
                const isOver = sec.is_over_limit;
                const shiftColor = sec.delta_weight > 0 ? "#00e676" : sec.delta_weight < 0 ? "#ff5252" : "#8b949e";
                const shiftSign = sec.delta_weight > 0 ? "+" : "";
                
                const limitBadge = isOver
                    ? `<span style="background: rgba(255, 82, 82, 0.15); color: #ff5252; border: 1px solid #ff5252; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.74rem;">⚠️ Over Limit (${sec.current_weight}% > 25%)</span>`
                    : `<span style="background: rgba(0, 230, 118, 0.15); color: #00e676; border: 1px solid #00e676; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.74rem;">✅ Within Limit (≤25%)</span>`;

                const stocksTags = sec.stocks.map(st => `<span style="background: #21262d; color: #58a6ff; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; margin-right: 4px;">${st}</span>`).join("");

                return `
                    <tr style="border-bottom: 1px solid #21262d;">
                        <td style="padding: 10px 8px; font-weight: 600; color: #fff;">${sec.sector}</td>
                        <td style="padding: 10px 8px;">${stocksTags}</td>
                        <td style="padding: 10px 8px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                                <span style="color: #fff; font-weight: 600;">${sec.current_weight}%</span>
                                <span style="color: #8b949e; font-size: 0.75rem;">₹${formatINR(sec.current_inr)}</span>
                            </div>
                            <div style="background: #21262d; border-radius: 3px; height: 5px; width: 100%; position: relative;">
                                <div style="background: ${isOver ? '#ff5252' : '#388bfd'}; height: 100%; width: ${Math.min(100, sec.current_weight)}%; border-radius: 3px;"></div>
                                <div style="position: absolute; left: 25%; top: -3px; bottom: -3px; width: 1.5px; background: #e3b341;" title="25% Institutional Threshold"></div>
                            </div>
                        </td>
                        <td style="padding: 10px 8px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                                <span style="color: #00e676; font-weight: 600;">${sec.optimal_weight}%</span>
                                <span style="color: #8b949e; font-size: 0.75rem;">₹${formatINR(sec.optimal_inr)}</span>
                            </div>
                            <div style="background: #21262d; border-radius: 3px; height: 5px; width: 100%; position: relative;">
                                <div style="background: #00e676; height: 100%; width: ${Math.min(100, sec.optimal_weight)}%; border-radius: 3px;"></div>
                                <div style="position: absolute; left: 25%; top: -3px; bottom: -3px; width: 1.5px; background: #e3b341;" title="25% Institutional Threshold"></div>
                            </div>
                        </td>
                        <td style="padding: 10px 8px; color: ${shiftColor}; font-weight: bold;">
                            ${shiftSign}${sec.delta_weight}%
                        </td>
                        <td style="padding: 10px 8px; text-align: center;">
                            ${limitBadge}
                        </td>
                    </tr>
                `;
            }).join("");
        }

        drawSectorDonutPlot();
    }

    function drawSectorDonutPlot() {
        if (!cachedSectorData) return;
        const sectors = cachedSectorData.sectors;
        const labels = sectors.map(s => s.sector);
        const curValues = sectors.map(s => s.current_weight);
        const optValues = sectors.map(s => s.optimal_weight);
        const colors = sectors.map(s => sectorColorsMap[s.sector] || "#8b949e");

        const chartEl = document.getElementById("portfolio-sector-chart");
        if (!chartEl) return;

        if (currentSectorViewMode === "dual") {
            const traceCur = {
                values: curValues,
                labels: labels,
                type: "pie",
                hole: 0.55,
                domain: { x: [0, 0.48] },
                name: "Current Sector Exposure",
                marker: { colors: colors },
                textinfo: "label+percent",
                textposition: "inside",
                insidetextorientation: "radial",
                textfont: { size: 10, color: "#fff" },
                hovertemplate: "<b>Current: %{label}</b><br>Weight: %{percent}<extra></extra>"
            };

            const traceOpt = {
                values: optValues,
                labels: labels,
                type: "pie",
                hole: 0.55,
                domain: { x: [0.52, 1.0] },
                name: "AI Optimal Sector Exposure",
                marker: { colors: colors },
                textinfo: "label+percent",
                textposition: "inside",
                insidetextorientation: "radial",
                textfont: { size: 10, color: "#fff" },
                hovertemplate: "<b>AI Optimal: %{label}</b><br>Weight: %{percent}<extra></extra>"
            };

            const layout = {
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                font: { color: "#8b949e", family: "Inter, sans-serif" },
                margin: { l: 20, r: 20, t: 30, b: 20 },
                showlegend: true,
                legend: { orientation: "h", y: -0.1, x: 0.5, xanchor: "center", font: { size: 10 } },
                annotations: [
                    {
                        text: "<b style='color:#58a6ff;'>Current</b><br><span style='font-size:10px;'>Portfolio</span>",
                        showarrow: false,
                        font: { size: 13, color: "#fff" },
                        x: 0.24, y: 0.5
                    },
                    {
                        text: "<b style='color:#00e676;'>AI Optimal</b><br><span style='font-size:10px;'>Portfolio</span>",
                        showarrow: false,
                        font: { size: 13, color: "#fff" },
                        x: 0.76, y: 0.5
                    }
                ]
            };

            chartEl.innerHTML = "";
            Plotly.newPlot("portfolio-sector-chart", [traceCur, traceOpt], layout, { responsive: true });
        } else {
            const traceCur = {
                values: curValues,
                labels: labels,
                type: "pie",
                hole: 0.42,
                domain: { x: [0.12, 0.88], y: [0.12, 0.88] },
                name: "Current (Inner)",
                marker: { colors: colors },
                textinfo: "percent",
                textposition: "inside",
                textfont: { size: 9, color: "#fff" },
                hovertemplate: "<b>Current: %{label}</b><br>Weight: %{percent}<extra></extra>"
            };

            const traceOpt = {
                values: optValues,
                labels: labels,
                type: "pie",
                hole: 0.70,
                domain: { x: [0, 1.0], y: [0, 1.0] },
                name: "AI Optimal (Outer)",
                marker: { colors: colors },
                textinfo: "percent",
                textposition: "inside",
                textfont: { size: 10, color: "#fff" },
                hovertemplate: "<b>AI Optimal: %{label}</b><br>Weight: %{percent}<extra></extra>"
            };

            const layout = {
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                font: { color: "#8b949e", family: "Inter, sans-serif" },
                margin: { l: 20, r: 20, t: 20, b: 20 },
                showlegend: true,
                legend: { orientation: "h", y: -0.1, x: 0.5, xanchor: "center", font: { size: 10 } },
                annotations: [
                    {
                        text: "<span style='font-size:11px; color:#8b949e;'>Inner: Current<br>Outer: AI</span>",
                        showarrow: false,
                        font: { size: 11, color: "#fff" },
                        x: 0.5, y: 0.5
                    }
                ]
            };

            chartEl.innerHTML = "";
            Plotly.newPlot("portfolio-sector-chart", [traceCur, traceOpt], layout, { responsive: true });
        }
    }

    // -------------------------------------------------------------------------
    // --- 2d. Historical Backtest of Rebalanced Portfolio (Equity Curve) ------
    // -------------------------------------------------------------------------
    function renderHistoricalBacktest(btData) {
        if (!btData) return;
        cachedBacktestData = btData;

        const m = btData.metrics;
        const cur = m.current;
        const opt = m.optimal;
        const bench = m.benchmark;

        const elCum = document.getElementById("bt-cum-ret-val");
        if (elCum) elCum.innerHTML = `${opt.cum_return_pct}%`;
        const elCumSub = document.getElementById("bt-cum-ret-sub");
        if (elCumSub) elCumSub.innerHTML = `vs Current: <span style="color:#58a6ff;">${cur.cum_return_pct}%</span> | NIFTY: ${bench.cum_return_pct}%`;

        const elCagr = document.getElementById("bt-cagr-val");
        if (elCagr) elCagr.innerHTML = `${opt.cagr_pct}%`;
        const elCagrSub = document.getElementById("bt-cagr-sub");
        if (elCagrSub) elCagrSub.innerHTML = `Current CAGR: <span style="color:#58a6ff;">${cur.cagr_pct}%</span>`;

        const elMaxDd = document.getElementById("bt-max-dd-val");
        if (elMaxDd) elMaxDd.innerHTML = `${opt.max_drawdown_pct}%`;
        const elMaxDdSub = document.getElementById("bt-max-dd-sub");
        if (elMaxDdSub) elMaxDdSub.innerHTML = `Current: <span style="color:#ff7b72;">${cur.max_drawdown_pct}%</span>`;

        const elSharpe = document.getElementById("bt-sharpe-val");
        if (elSharpe) elSharpe.innerHTML = `${opt.sharpe_ratio}`;
        const elSharpeSub = document.getElementById("bt-sharpe-sub");
        if (elSharpeSub) elSharpeSub.innerHTML = `Current: <span style="color:#58a6ff;">${cur.sharpe_ratio}</span>`;

        const elAlpha = document.getElementById("bt-alpha-val");
        if (elAlpha) elAlpha.innerHTML = `+₹${formatINR(m.alpha_inr)}`;
        const elAlphaSub = document.getElementById("bt-alpha-sub");
        if (elAlphaSub) elAlphaSub.innerHTML = `+${m.alpha_pct}% historical excess alpha`;

        drawBacktestPlot();
    }

    function drawBacktestPlot() {
        if (!cachedBacktestData) return;
        const dates = cachedBacktestData.dates;
        const cEq = cachedBacktestData.current_equity;
        const oEq = cachedBacktestData.optimal_equity;
        const bEq = cachedBacktestData.benchmark_equity;

        let sliceIdx = 0;
        const totalPoints = dates.length;
        if (currentHorizon === "1y") {
            sliceIdx = Math.max(0, totalPoints - 126);
        } else if (currentHorizon === "2y") {
            sliceIdx = Math.max(0, totalPoints - 252);
        } else if (currentHorizon === "3y") {
            sliceIdx = Math.max(0, totalPoints - 378);
        }

        const subDates = dates.slice(sliceIdx);
        const subCEq = cEq.slice(sliceIdx);
        const subOEq = oEq.slice(sliceIdx);
        const subBEq = bEq.slice(sliceIdx);

        const traceCur = {
            x: subDates,
            y: subCEq,
            mode: "lines",
            name: "Current Allocation",
            line: { color: "#388bfd", width: 2.2 },
            hovertemplate: "<b>Current Allocation</b>: ₹%{y:,.0f}<extra></extra>"
        };

        const traceOpt = {
            x: subDates,
            y: subOEq,
            mode: "lines",
            name: "AI-Rebalanced Allocation",
            line: { color: "#00e676", width: 2.8 },
            hovertemplate: "<b>AI-Rebalanced</b>: ₹%{y:,.0f}<extra></extra>"
        };

        const traceBench = {
            x: subDates,
            y: subBEq,
            mode: "lines",
            name: "NIFTY 50 Benchmark",
            line: { color: "#8b949e", width: 1.6, dash: "dot" },
            hovertemplate: "<b>NIFTY 50 Benchmark</b>: ₹%{y:,.0f}<extra></extra>"
        };

        const layout = {
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: { color: "#8b949e", family: "Inter, sans-serif" },
            margin: { l: 70, r: 20, t: 25, b: 45 },
            xaxis: {
                gridcolor: "rgba(48, 54, 61, 0.4)",
                tickfont: { color: "#fff", size: 10 }
            },
            yaxis: {
                title: { text: "Portfolio Equity Value (₹)", font: { size: 11, color: "#8b949e" } },
                gridcolor: "rgba(48, 54, 61, 0.4)",
                tickprefix: "₹",
                tickformat: ",.0f"
            },
            legend: { orientation: "h", y: 1.12, x: 0.5, xanchor: "center", font: { size: 11 } },
            hovermode: "x unified"
        };

        const chartEl = document.getElementById("portfolio-backtest-chart");
        if (chartEl) {
            chartEl.innerHTML = "";
            Plotly.newPlot("portfolio-backtest-chart", [traceCur, traceOpt, traceBench], layout, { responsive: true });
        }
    }

    // --- Wire Feature Buttons & Interactivity ---

    // Toggle Donut View Mode
    const toggleDonutBtn = document.getElementById("btn-toggle-donut-view");
    if (toggleDonutBtn) {
        toggleDonutBtn.addEventListener("click", () => {
            currentSectorViewMode = currentSectorViewMode === "dual" ? "concentric" : "dual";
            const txt = document.getElementById("toggle-donut-text");
            if (txt) {
                txt.innerText = currentSectorViewMode === "dual" ? "Toggle: Concentric Donut" : "Toggle: Dual Donut";
            }
            drawSectorDonutPlot();
        });
    }

    // Horizon filter buttons
    document.querySelectorAll(".btn-time-filter").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".btn-time-filter").forEach(b => {
                b.classList.remove("active");
                b.style.background = "#161b22";
                b.style.color = "#8b949e";
                b.style.borderColor = "#30363d";
            });
            const target = e.currentTarget;
            target.classList.add("active");
            target.style.background = "#21262d";
            target.style.color = "#58a6ff";
            target.style.borderColor = "#58a6ff";
            currentHorizon = target.getAttribute("data-horizon");
            drawBacktestPlot();
        });
    });

    // "Apply AI Weights" Button
    const btnApplyRebalance = document.getElementById("btn-apply-rebalance");
    if (btnApplyRebalance) {
        btnApplyRebalance.addEventListener("click", () => {
            if (!latestPortfolioData || !latestPortfolioData.rebalance_recommendations) return;
            const recs = latestPortfolioData.rebalance_recommendations;
            
            // Overwrite input weights with optimal_weight
            recs.forEach(rec => {
                const holding = portfolioHoldings.find(h => h.ticker === rec.ticker);
                if (holding) {
                    holding.weight = Math.round(rec.optimal_weight);
                }
            });

            // Ensure exact 100% sum
            let sumW = portfolioHoldings.reduce((s, h) => s + h.weight, 0);
            if (sumW !== 100 && portfolioHoldings.length > 0) {
                portfolioHoldings[0].weight += (100 - sumW);
            }

            // Re-render table
            renderPortfolioTable();
            
            btnApplyRebalance.innerHTML = `<i class="fa-solid fa-check" style="margin-right: 5px;"></i> Weights Applied!`;
            btnApplyRebalance.style.opacity = "0.7";
            setTimeout(() => {
                btnApplyRebalance.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles" style="margin-right: 5px;"></i> Apply AI Weights`;
                btnApplyRebalance.style.opacity = "1";
            }, 2500);

            // Automatically trigger live optimization with applied weights
            const runBtn = document.getElementById("run-portfolio-btn");
            if (runBtn) runBtn.click();
        });
    }

    // Initialize Portfolio table on page load
    renderPortfolioTable();

});
