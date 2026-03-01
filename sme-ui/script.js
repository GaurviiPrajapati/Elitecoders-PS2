document.addEventListener('DOMContentLoaded', () => {
    // Get Started logic
    const getStartedBtn = document.getElementById('get-started-btn');
    const sidebar = document.getElementById('sidebar');
    const taskbar = document.getElementById('taskbar');
    const chatInputContainer = document.getElementById('chat-input-container');

    if (getStartedBtn) {
        getStartedBtn.addEventListener('click', () => {
            // Animate button out
            getStartedBtn.style.transform = 'scale(0.8)';
            getStartedBtn.style.opacity = '0';
            getStartedBtn.style.margin = '0';
            getStartedBtn.style.padding = '0';
            getStartedBtn.style.height = '0';
            getStartedBtn.style.overflow = 'hidden';

            setTimeout(() => {
                getStartedBtn.style.display = 'none';

                // Reveal and animate UI components in a staggered sequence
                if (taskbar) {
                    taskbar.classList.remove('ui-hidden');
                    taskbar.classList.add('animate-down');
                }

                if (sidebar) {
                    sidebar.classList.remove('ui-hidden');
                    sidebar.classList.add('animate-right');
                }

                if (chatInputContainer) {
                    chatInputContainer.classList.remove('ui-hidden');
                    chatInputContainer.classList.add('animate-up');
                }
            }, 600); // wait for button to fade completely
        });
    }

    // Sidebar logic
    const sidebarToggle = document.getElementById('sidebar-toggle');

    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // New Chat logic
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', (e) => {
            const newChatId = Date.now().toString();
            if (window.location.pathname.endsWith('chat.html')) {
                e.preventDefault();
                switchChat(newChatId);
            } else {
                window.location.href = `chat.html?chatId=${newChatId}`;
            }
        });
    }

    // Sidebar Dropdown logics
    const personaDropdownBtn = document.getElementById('persona-dropdown-btn');
    if (personaDropdownBtn) {
        const personaDropdownContainer = personaDropdownBtn.closest('.nav-dropdown');
        personaDropdownBtn.addEventListener('click', () => {
            personaDropdownContainer.classList.toggle('active');
        });
    }

    const modelDropdownBtn = document.getElementById('model-dropdown-btn');
    if (modelDropdownBtn) {
        const modelDropdownContainer = modelDropdownBtn.closest('.nav-dropdown');
        modelDropdownBtn.addEventListener('click', () => {
            modelDropdownContainer.classList.toggle('active');
        });
    }

    // Model Selection logic
    const modelItems = document.querySelectorAll('#model-dropdown-content .nav-item');
    modelItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            modelItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');

            const modelName = this.textContent.trim();
            addMessage(`AI Model swapped to ${modelName}.`, 'system');
        });
    });

    // Theme logic
    const themeToggle = document.getElementById('theme-toggle');

    if (themeToggle) {
        themeToggle.addEventListener('change', () => {
            themeToggle.classList.remove('pristine');
            if (themeToggle.checked) {
                document.body.classList.add('light-mode');
            } else {
                document.body.classList.remove('light-mode');
            }
        });
    }

    // Logout logic
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('expertEaseToken');
            localStorage.removeItem('expertEaseUser');
            window.location.replace('login.html');
        });
    }

    // Chat logic
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const chatAnchor = document.getElementById('chat-anchor');
    // API Endpoints
    const API_BASE_URL = 'http://localhost:5000/api';

    // Figure out the current Chat ID
    let currentChatId = null;
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('chatId')) {
        currentChatId = urlParams.get('chatId');
        localStorage.setItem('expertEaseCurrentChatId', currentChatId);
    } else {
        currentChatId = localStorage.getItem('expertEaseCurrentChatId') || Date.now().toString();
        localStorage.setItem('expertEaseCurrentChatId', currentChatId);
        // Only modify URL if we are actually on chat.html
        if (window.location.pathname.endsWith('chat.html')) {
            window.history.replaceState({}, '', `chat.html?chatId=${currentChatId}`);
        }
    }

    async function loadRecentChats() {
        const token = localStorage.getItem('expertEaseToken');
        if (!token) return;

        try {
            const res = await fetch(`${API_BASE_URL}/chat-sessions`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const sessions = await res.json();
                const container = document.getElementById('recent-chats-container');
                if (container) {
                    container.innerHTML = ''; // clear out placeholder
                    sessions.forEach(session => {
                        const link = document.createElement('a');
                        link.href = `chat.html?chatId=${session._id}`;
                        link.classList.add('nav-item');
                        if (session._id === currentChatId && window.location.pathname.endsWith('chat.html')) {
                            link.classList.add('active');
                        }

                        let displayTitle = session.firstMessage;

                        link.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; margin-right: 0.5rem;"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg> <span style="font-size: 0.85rem; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${displayTitle}</span>`;

                        link.addEventListener('click', (e) => {
                            if (window.location.pathname.endsWith('chat.html')) {
                                e.preventDefault();
                                if (currentChatId !== session._id) {
                                    switchChat(session._id);
                                }
                            }
                        });

                        container.appendChild(link);
                    });
                }
            }
        } catch (err) {
            console.error('Could not load recent chats', err);
        }
    }

    async function loadChatHistory() {
        const token = localStorage.getItem('expertEaseToken');
        if (!token) return;

        try {
            const res = await fetch(`${API_BASE_URL}/chats/${currentChatId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const messages = await res.json();
                messages.forEach(msg => {
                    const msgDiv = document.createElement('div');
                    msgDiv.classList.add('message', msg.role);
                    msgDiv.textContent = msg.content;
                    msgDiv.style.opacity = '1';
                    msgDiv.style.transform = 'translateY(0)';

                    chatMessages.insertBefore(msgDiv, chatAnchor);
                });
                if (messages.length > 0) {
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                    // Hide intro if there's history
                    const pageContent = document.getElementById('page-content');
                    if (pageContent) pageContent.classList.add('ui-hidden');
                }
            }
        } catch (err) {
            console.error('Could not load chat history', err);
        }
    }

    async function saveMessageToDB(role, content) {
        const token = localStorage.getItem('expertEaseToken');
        if (!token) return;

        try {
            await fetch(`${API_BASE_URL}/chats`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ chatId: currentChatId, role, content })
            });
            // Reload recent chats list to show new message if it's the first one
            loadRecentChats();
        } catch (err) {
            console.error('Failed to save message', err);
        }
    }

    async function switchChat(newChatId) {
        if (!chatMessages) return;

        // 1. Fade out current chat messages
        chatMessages.style.opacity = '0';

        // Wait for CSS transition (0.5s)
        setTimeout(async () => {
            currentChatId = newChatId;
            localStorage.setItem('expertEaseCurrentChatId', currentChatId);
            window.history.pushState({}, '', `chat.html?chatId=${currentChatId}`);

            // Clear current chat DOM
            const msgs = chatMessages.querySelectorAll('.message');
            msgs.forEach(m => m.remove());

            // Re-show intro text by default, loadChatHistory will hide it again if messages are fetched
            const pageContent = document.getElementById('page-content');
            if (pageContent) {
                pageContent.classList.remove('ui-hidden');
                pageContent.style.opacity = '1';
            }

            // Sidebar active state logic
            const allNavItems = document.querySelectorAll('#recent-chats-container .nav-item');
            allNavItems.forEach(item => item.classList.remove('active'));
            const activeLink = document.querySelector(`#recent-chats-container a[href="chat.html?chatId=${currentChatId}"]`);
            if (activeLink) activeLink.classList.add('active');

            await loadChatHistory();

            // 2. Fade back in
            chatMessages.style.opacity = '1';
        }, 500);
    }

    // Load history and sidebar on startup
    if (chatMessages) {
        loadChatHistory();
    }
    loadRecentChats();

    function addMessage(text, sender) {
        if (!text.trim()) return;

        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender);
        msgDiv.textContent = text;

        // Intro animation
        msgDiv.style.opacity = '0';
        msgDiv.style.transform = 'translateY(10px)';
        msgDiv.style.transition = 'all 0.3s ease-out';

        chatMessages.insertBefore(msgDiv, chatAnchor);

        setTimeout(() => {
            msgDiv.style.opacity = '1';
            msgDiv.style.transform = 'translateY(0)';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 10);
    }

    function handleSend() {
        const text = chatInput.value;
        if (text) {
            // Hide intro content when first message is sent
            const pageContent = document.getElementById('page-content');
            if (pageContent && !pageContent.classList.contains('ui-hidden')) {
                pageContent.style.opacity = '0';
                setTimeout(() => {
                    pageContent.classList.add('ui-hidden');
                }, 150);
            }

            addMessage(text, 'user');
            saveMessageToDB('user', text);
            chatInput.value = '';

            // Show thinking bubble
            const thinkingDiv = document.createElement('div');
            thinkingDiv.classList.add('message', 'bot', 'thinking-bubble');
            thinkingDiv.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';

            thinkingDiv.style.opacity = '0';
            thinkingDiv.style.transform = 'translateY(10px)';
            thinkingDiv.style.transition = 'all 0.3s ease-out';

            chatMessages.insertBefore(thinkingDiv, chatAnchor);

            setTimeout(() => {
                thinkingDiv.style.opacity = '1';
                thinkingDiv.style.transform = 'translateY(0)';
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 10);

            // Simulate bot response
            setTimeout(() => {
                thinkingDiv.style.opacity = '0';
                thinkingDiv.style.transform = 'translateY(10px)';
                setTimeout(() => {
                    thinkingDiv.remove();
                    const botReply = 'Processed by ExpertEASE Governance Layer. Reasoning recorded. Proceeding with safe output.';
                    addMessage(botReply, 'bot');
                    saveMessageToDB('bot', botReply);
                }, 300);
            }, 1800);
        }
    }

    sendBtn.addEventListener('click', handleSend);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    });

    // SPA Page Database structure for seamless loading
    const pages = {
        'dashboard': {
            badge: 'Middleware Solution',
            title: 'Accountable AI Decision Systems',
            body: `
                <p>
                    From PS-02, we understood that the core problem is not generating better answers, but controlling
                    how AI agents reason when operating in high-stakes, domain-specific scenarios. General-purpose
                    agents tend to hallucinate or over-generalize because they lack enforceable domain logic and
                    verifiable sources of truth.
                </p>
                <p>
                    This hot-swappable ExpertEASE layer acts as a governance and reasoning
                    middleware—injecting domain-specific decision frameworks, validating outputs against real-world
                    standards and live data sources, and blocking responses that cannot be justified. Transforms AI
                    agents from probabilistic guessers into accountable, auditable decision systems suitable for
                    real-world deployment.
                </p>
            `
        },
        'technical': {
            badge: 'Active Persona',
            title: 'Technical Mode Interface',
            body: `
                <p>
                    <strong>Target Audience:</strong> Engineers, System Administrators, API Integrators.
                </p>
                <p>
                    In Technical Mode, ExpertEASE provides verbose execution logging, architecture trace logic, deep schema validation reports, and raw JSON-formatted reasoning outputs. All high-level fluff is bypassed so the AI delivers direct, actionable implementation structures suitable for debugging complex pipelines.
                </p>
            `
        },
        'executive': {
            badge: 'Active Persona',
            title: 'Executive Mode Dashboard',
            body: `
                <p>
                    <strong>Target Audience:</strong> C-Suite, Decision Makers, Project Managers.
                </p>
                <p>
                    Executive Mode distills complex AI operations into high-level strategic summaries. The reasoning engine condenses technical findings into risk assessments, ROI impacts, and bottleneck identifications. Verbosity is significantly reduced, prioritizing key insights over intricate code mechanics.
                </p>
            `
        },
        'audit': {
            badge: 'Active Persona',
            title: 'Audit & Compliance Flow',
            body: `
                <p>
                    <strong>Target Audience:</strong> Compliance Officers, Legal Teams, Security Auditors.
                </p>
                <p>
                    Audit Mode strictly enforces responses mapped accurately against verified policy datasets and legal constraints. Every single AI-generated claim is tagged with its source node. Outputs that fail to meet strict validation parameters or that attempt probabilistic guessing are explicitly blocked.
                </p>
            `
        },
        'client': {
            badge: 'Active Persona',
            title: 'Client-Facing Environment',
            body: `
                <p>
                    <strong>Target Audience:</strong> Consumers, Vendors, Support Tiers.
                </p>
                <p>
                    This persona shifts the AI tonality out of internal-admin scope into a polished, brand-safe, empathetic voice. Reasoning steps are fully sanitized so proprietary backend data models aren't exposed. ExpertEASE guarantees the AI maintains consistent corporate messaging safeguards.
                </p>
            `
        },
        'settings': {
            badge: 'Admin Panel',
            title: 'System Settings',
            body: `
                <p>Configuration panel for ExpertEASE Core. Update API keys, manage latency thresholds, and access physical logic swap mechanisms.</p>
            `
        }
    };

    // Advanced Page Routing
    const navItems = document.querySelectorAll('.nav-item');
    const pageContentNode = document.getElementById('page-content');

    navItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();

            const targetPage = this.getAttribute('data-page');

            // If we click on it again, it should toggle off (go back to default dashboard)
            if (this.classList.contains('active')) {
                if (targetPage !== 'dashboard') {
                    this.classList.remove('active');
                    const dashboardItem = document.querySelector('.nav-item[data-page="dashboard"]');
                    if (dashboardItem) dashboardItem.classList.add('active');

                    addMessage('System Protocol Reverted to Default.', 'system');
                }
                return;
            }

            // Move to other mode
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');

            if (targetPage && pages[targetPage] && pageContentNode) {
                const newData = pages[targetPage];

                if (['technical', 'executive', 'audit', 'client'].includes(targetPage)) {
                    addMessage(`System Protocol Overridden to: ${newData.title}.`, 'system');
                    setTimeout(() => {
                        addMessage(`ExpertEASE is now operating precisely under ${targetPage} protocols. Formats locked in.`, 'bot');
                    }, 500);
                }
            }
        });
    });
});
