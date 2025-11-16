// ===================================
// MODERN WHATSAPP BOT DASHBOARD
// Enhanced with glassmorphism UI
// ===================================

const API_BASE_URL = window.location.origin;
const REFRESH_INTERVAL = 10000; // 10 seconds

// State management
const state = {
    chats: [],
    expandedChats: new Set(),
    expandedLogs: new Set(),
    expandedMessages: new Set(),
    refreshTimer: null,
    currentView: 'dashboard',
    searchQuery: ''
};

// ===================================
// INITIALIZATION
// ===================================

async function init() {
    console.log('🚀 Initializing modern dashboard...');
    
    setupEventListeners();
    await loadChats();
    startAutoRefresh();
    updateDashboardStats();
}

function setupEventListeners() {
    // Sidebar navigation
    document.querySelectorAll('.nav-item, .bottom-nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            switchView(view);
        });
    });

    // Mobile menu
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const closeSidebar = document.getElementById('closeSidebar');
    const mobileOverlay = document.getElementById('mobileOverlay');
    const sidebar = document.getElementById('sidebar');

    mobileMenuBtn?.addEventListener('click', () => {
        sidebar.classList.add('active');
        mobileOverlay.classList.add('active');
    });

    closeSidebar?.addEventListener('click', () => {
        sidebar.classList.remove('active');
        mobileOverlay.classList.remove('active');
    });

    mobileOverlay?.addEventListener('click', () => {
        sidebar.classList.remove('active');
        mobileOverlay.classList.remove('active');
    });

    // Quick actions
    document.getElementById('syncChatsBtn')?.addEventListener('click', syncChats);
    document.getElementById('refreshBtn')?.addEventListener('click', () => loadChats());
    
    // Add chat form
    document.getElementById('addChatBtn')?.addEventListener('click', toggleAddChatForm);
    document.getElementById('closeAddChat')?.addEventListener('click', toggleAddChatForm);
    document.getElementById('submitAddChat')?.addEventListener('click', addChatManually);

    // Search
    document.getElementById('searchChats')?.addEventListener('input', (e) => {
        state.searchQuery = e.target.value.toLowerCase();
        if (state.currentView === 'bots') {
            displayBotsView();
        } else {
            filterChats();
        }
    });

    // Enter key on chat inputs
    document.getElementById('manualChatJid')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addChatManually();
    });
    document.getElementById('manualChatName')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addChatManually();
    });
}

// ===================================
// VIEW MANAGEMENT
// ===================================

function switchView(view) {
    state.currentView = view;
    
    // Clear search when switching views
    state.searchQuery = '';
    const searchInput = document.getElementById('searchChats');
    if (searchInput) searchInput.value = '';
    
    // Update active nav items
    document.querySelectorAll('.nav-item, .bottom-nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === view);
    });

    // Update page title
    const titles = {
        dashboard: 'Dashboard',
        chats: 'Chats',
        bots: 'Bots'
    };
    const subtitles = {
        dashboard: 'Overview of your bot operations',
        chats: 'Manage your WhatsApp chats',
        bots: 'Control your bot instances'
    };

    document.getElementById('pageTitle').textContent = titles[view] || 'Dashboard';
    document.getElementById('pageSubtitle').textContent = subtitles[view] || '';

    // Show/hide sections based on view
    const dashboardOverview = document.getElementById('dashboardOverview');
    const chatsSection = document.querySelector('.chats-section');
    
    if (view === 'dashboard') {
        dashboardOverview.style.display = 'block';
        chatsSection.style.display = 'block';
        if (searchInput) searchInput.placeholder = 'Search chats...';
        displayChats(state.chats);
    } else if (view === 'chats') {
        dashboardOverview.style.display = 'none';
        chatsSection.style.display = 'block';
        if (searchInput) searchInput.placeholder = 'Search chats...';
        displayChats(state.chats);
    } else if (view === 'bots') {
        dashboardOverview.style.display = 'none';
        chatsSection.style.display = 'block';
        if (searchInput) searchInput.placeholder = 'Search bots...';
        displayBotsView();
    }

    // Close mobile menu
    document.getElementById('sidebar')?.classList.remove('active');
    document.getElementById('mobileOverlay')?.classList.remove('active');
}

// ===================================
// TOAST NOTIFICATIONS
// ===================================

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✓',
        error: '✗',
        info: 'ℹ',
        warning: '⚠'
    };

    const titles = {
        success: 'Success',
        error: 'Error',
        info: 'Info',
        warning: 'Warning'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-title">${titles[type] || titles.info}</div>
            <div class="toast-message">${escapeHtml(message)}</div>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ===================================
// DATA LOADING
// ===================================

async function loadChats() {
    try {
        showLoading();
        hideError();
        
        const response = await fetch(`${API_BASE_URL}/chats`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        state.chats = await response.json();
        console.log('✓ Loaded chats:', state.chats.length);
        
        if (state.chats.length === 0) {
            showNoChats();
        } else {
            // Chats start closed by default
            displayChats(state.chats);
        }
        
        updateDashboardStats();
        hideLoading();
        
    } catch (error) {
        console.error('Error loading chats:', error);
        showError('Failed to load chats: ' + error.message);
        hideLoading();
    }
}

async function loadChatsQuietly() {
    try {
        const response = await fetch(`${API_BASE_URL}/chats`);
        if (!response.ok) return;
        
        const chats = await response.json();
        
        // Check if chat list changed
        const currentChatIds = state.chats.map(c => c.chat_jid).sort();
        const newChatIds = chats.map(c => c.chat_jid).sort();
        
        const chatsChanged = JSON.stringify(currentChatIds) !== JSON.stringify(newChatIds);
        
        if (chatsChanged) {
            state.chats = chats;
            displayChats(chats);
            updateDashboardStats();
        } else {
            state.chats = chats;
            updateBotStatuses(chats);
            updateDashboardStats();
        }
    } catch (error) {
        console.debug('Auto-refresh failed:', error);
    }
}

// ===================================
// DASHBOARD STATS
// ===================================

function updateDashboardStats() {
    const totalChats = state.chats.length;
    let runningBots = 0;
    let enabledBots = 0;
    const availableBotTypes = new Set();

    state.chats.forEach(chat => {
        chat.bots?.forEach(bot => {
            availableBotTypes.add(bot.name);
            if (bot.status === 'running') runningBots++;
            if (bot.enabled) enabledBots++;
        });
    });

    // Update stats cards
    document.getElementById('totalChats').textContent = totalChats;
    document.getElementById('runningBots').textContent = runningBots;
    document.getElementById('enabledBots').textContent = enabledBots;
    document.getElementById('availableBots').textContent = availableBotTypes.size;

    // Update sidebar stats
    document.getElementById('statsRunning').textContent = runningBots;
    document.getElementById('statsStopped').textContent = enabledBots - runningBots;

    // Update badges
    document.getElementById('chatsCount').textContent = totalChats;
    document.getElementById('botsCount').textContent = availableBotTypes.size;
}

// ===================================
// DISPLAY FUNCTIONS
// ===================================

function displayChats(chats) {
    const container = document.getElementById('chats-container');
    const sectionHeaderBar = document.querySelector('.section-header-bar');
    
    // Update section title
    const titleElement = sectionHeaderBar?.querySelector('.section-title-large');
    if (titleElement) {
        titleElement.textContent = 'Your Chats';
    }
    
    const filteredChats = state.searchQuery 
        ? chats.filter(chat => 
            chat.chat_name.toLowerCase().includes(state.searchQuery) ||
            chat.chat_jid.toLowerCase().includes(state.searchQuery)
          )
        : chats;

    if (filteredChats.length === 0 && state.searchQuery) {
        container.innerHTML = `
            <div class="empty-state glass-card" style="grid-column: 1 / -1;">
                <div class="empty-icon">🔍</div>
                <h3 class="empty-title">No matches found</h3>
                <p class="empty-text">Try a different search term</p>
            </div>
        `;
    } else {
        container.innerHTML = filteredChats.map(chat => createChatCard(chat)).join('');
    }
    
    // Refresh logs for expanded bots
    for (const key of state.expandedLogs) {
        const [botName, chatJid] = key.split('::');
        loadBotLogs(botName, chatJid);
    }
    
    // Refresh messages for expanded chats
    for (const chatJid of state.expandedMessages) {
        loadChatMessages(chatJid);
    }
    
    document.getElementById('no-chats').style.display = 'none';
    container.style.display = 'grid';
}

function createChatCard(chat) {
    const isExpanded = state.expandedChats.has(chat.chat_jid);
    const expandedClass = isExpanded ? 'expanded' : '';
    const enabledCount = chat.bots.filter(b => b.enabled).length;
    const runningCount = chat.bots.filter(b => b.status === 'running').length;
    const safeJid = makeSafeId(chat.chat_jid);
    const messagesVisible = state.expandedMessages.has(chat.chat_jid);

    const botsHtml = chat.bots && chat.bots.length > 0
        ? chat.bots.map(bot => createBotCard(bot, chat.chat_jid)).join('')
        : `<div class="empty-state" style="grid-column: 1 / -1; padding: 2rem;">
            <div class="empty-icon" style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
            <p style="color: var(--text-muted);">No bots discovered yet</p>
           </div>`;
    
    return `
        <div class="chat-card ${expandedClass}" data-chat-jid="${chat.chat_jid}">
            <!-- Messages Section -->
            <div class="messages-section ${messagesVisible ? 'visible' : ''}" id="messages-${safeJid}">
                <div class="messages-header">
                    <span class="messages-title">💬 Recent Messages</span>
                    <button class="messages-close-btn" onclick="toggleMessages('${escapeAttr(chat.chat_jid)}')">×</button>
                </div>
                <div class="messages-container" id="messages-container-${safeJid}">
                    <p style="color: var(--text-muted);">Loading messages...</p>
                </div>
            </div>

            <!-- Chat Header -->
            <div class="chat-card-header" onclick="toggleChat('${escapeAttr(chat.chat_jid)}')">
                <div class="chat-header-top">
                <div class="chat-info">
                        <div class="chat-name">${escapeHtml(chat.chat_name)}</div>
                    <div class="chat-jid">${chat.chat_jid}</div>
                    </div>
                    <button class="chat-expand-btn" onclick="event.stopPropagation();">
                        ▼
                    </button>
                </div>
                
                    ${chat.bots.length > 0 ? `
                    <div class="chat-stats">
                        <div class="chat-stat">
                            <span class="chat-stat-icon">🤖</span>
                            <span class="chat-stat-value">${chat.bots.length}</span>
                            <span class="chat-stat-label">bots</span>
                        </div>
                        <div class="chat-stat">
                            <span class="chat-stat-icon">✓</span>
                            <span class="chat-stat-value">${enabledCount}</span>
                            <span class="chat-stat-label">enabled</span>
                </div>
                        <div class="chat-stat">
                            <span class="chat-stat-icon">▶️</span>
                            <span class="chat-stat-value">${runningCount}</span>
                            <span class="chat-stat-label">running</span>
                        </div>
                    </div>
                ` : ''}
                
                <div class="chat-actions" onclick="event.stopPropagation();">
                    <button class="chat-action-btn" onclick="toggleMessages('${escapeAttr(chat.chat_jid)}')">
                        💬 Messages
                    </button>
                    <button class="chat-action-btn danger" onclick="deleteChat('${escapeAttr(chat.chat_jid)}')">
                        🗑️ Delete
                    </button>
                </div>
            </div>

            <!-- Bots Section -->
            <div class="bots-section">
            <div class="bots-grid">
                    ${botsHtml}
                </div>
            </div>
        </div>
    `;
}

function createBotCard(bot, chatJid) {
    const isRunning = bot.status === 'running';
    const isEnabled = bot.enabled || false;
    const uptimeText = bot.uptime_seconds ? formatUptime(bot.uptime_seconds) : 'N/A';
    const logsKey = `${bot.name}::${chatJid}`;
    const logsVisible = state.expandedLogs.has(logsKey);
    const safeJid = makeSafeId(chatJid);
    const safeLogsId = `${bot.name}-${safeJid}`;
    const runningClass = isRunning ? 'running' : '';
    
    return `
        <div class="bot-card ${runningClass}" data-bot-name="${bot.name}" data-chat-jid="${chatJid}">
            <div class="bot-header">
                <div class="bot-name">${escapeHtml(bot.display_name)}</div>
                <div class="bot-status-badge ${bot.status}">${bot.status}</div>
            </div>
            
            <div class="bot-info">
                <div class="bot-info-row">
                    <span class="bot-info-label">Prefix</span>
                    <span class="bot-info-value">${escapeHtml(bot.prefix)}</span>
                </div>
                <div class="bot-info-row">
                    <span class="bot-info-label">Uptime</span>
                    <span class="bot-info-value">${uptimeText}</span>
                </div>
            </div>
            
            <div class="bot-toggle">
                <span class="bot-toggle-label">Enable Bot</span>
                <label class="toggle-switch">
                    <input type="checkbox" 
                           ${isEnabled ? 'checked' : ''} 
                           onchange="toggleBotAssignment('${bot.name}', '${escapeAttr(chatJid)}', this.checked)">
                    <span class="toggle-slider"></span>
                </label>
            </div>
            
            <div class="bot-actions">
                <button class="bot-btn start" 
                        onclick="startBot('${bot.name}', '${escapeAttr(chatJid)}')" 
                        ${isRunning ? 'disabled' : ''}>
                    ▶️
                </button>
                <button class="bot-btn stop" 
                        onclick="stopBot('${bot.name}', '${escapeAttr(chatJid)}')" 
                        ${!isRunning ? 'disabled' : ''}>
                    ⏹️
                </button>
                <button class="bot-btn logs" 
                        onclick="toggleLogs('${bot.name}', '${escapeAttr(chatJid)}')"
                        ${!isRunning ? 'disabled' : ''}>
                    📋
                </button>
            </div>
            
            <div class="logs-section ${logsVisible ? 'visible' : ''}" id="logs-${safeLogsId}">
                <div class="logs-container" id="logs-container-${safeLogsId}">
                    <p style="color: var(--text-muted);">Loading logs...</p>
                </div>
            </div>
        </div>
    `;
}

function updateBotStatuses(chats) {
    chats.forEach(chat => {
        chat.bots?.forEach(bot => {
            const botCard = document.querySelector(`[data-bot-name="${bot.name}"][data-chat-jid="${chat.chat_jid}"]`);
            if (!botCard) return;
            
            // Update status badge
            const statusBadge = botCard.querySelector('.bot-status-badge');
            if (statusBadge) {
                statusBadge.className = `bot-status-badge ${bot.status}`;
                statusBadge.textContent = bot.status;
            }
            
            // Update card running class (both bot-card and bot-card-standalone)
            botCard.classList.toggle('running', bot.status === 'running');
            
            // Update uptime
            const uptimeValue = botCard.querySelector('.bot-info-row:nth-child(2) .bot-info-value');
            if (uptimeValue) {
                uptimeValue.textContent = bot.uptime_seconds ? formatUptime(bot.uptime_seconds) : 'N/A';
            }
            
            // Update buttons
            const isRunning = bot.status === 'running';
            const startBtn = botCard.querySelector('.bot-btn.start');
            const stopBtn = botCard.querySelector('.bot-btn.stop');
            const logsBtn = botCard.querySelector('.bot-btn.logs');
            
            if (startBtn) startBtn.disabled = isRunning;
            if (stopBtn) stopBtn.disabled = !isRunning;
            if (logsBtn) logsBtn.disabled = !isRunning;
            
            // Update toggle
            const toggle = botCard.querySelector('.toggle-switch input');
            if (toggle && toggle.checked !== bot.enabled) {
                toggle.checked = bot.enabled;
            }
        });
    });
}

// ===================================
// CHAT ACTIONS
// ===================================

function toggleChat(chatJid) {
    const chatCard = document.querySelector(`[data-chat-jid="${chatJid}"]`);
    if (!chatCard) return;
    
    if (chatCard.classList.contains('expanded')) {
        chatCard.classList.remove('expanded');
        state.expandedChats.delete(chatJid);
    } else {
        chatCard.classList.add('expanded');
        state.expandedChats.add(chatJid);
    }
}

async function syncChats() {
    const button = document.getElementById('syncChatsBtn');
    const originalHtml = button.innerHTML;
    
    button.disabled = true;
    button.innerHTML = '<span class="loading-spinner"></span><span class="btn-text">Syncing...</span>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/chats/sync`, { method: 'POST' });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to sync chats');
        }
        
        const result = await response.json();
        showToast(result.message, 'success');
        await loadChats();
        
    } catch (error) {
        console.error('Error syncing chats:', error);
        showToast(`Failed to sync: ${error.message}`, 'error');
    } finally {
        button.innerHTML = originalHtml;
            button.disabled = false;
    }
}

function toggleAddChatForm() {
    const section = document.getElementById('addChatSection');
    if (section.style.display === 'none') {
        section.style.display = 'block';
        document.getElementById('manualChatJid').focus();
    } else {
        section.style.display = 'none';
        document.getElementById('manualChatJid').value = '';
        document.getElementById('manualChatName').value = '';
    }
}

async function addChatManually() {
    const chatJidInput = document.getElementById('manualChatJid');
    const chatNameInput = document.getElementById('manualChatName');
    const button = document.getElementById('submitAddChat');
    
    const chatJid = chatJidInput.value.trim();
    const chatName = chatNameInput.value.trim();
    
    if (!chatJid) {
        chatJidInput.style.borderColor = 'var(--danger)';
        showToast('Please enter a chat JID', 'error');
        setTimeout(() => chatJidInput.style.borderColor = '', 2000);
        return;
    }
    
    const originalHtml = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="loading-spinner"></span><span class="btn-text">Adding...</span>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/chats`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_jid: chatJid, chat_name: chatName || null })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add chat');
        }
        
        showToast('Chat added successfully!', 'success');
        chatJidInput.value = '';
        chatNameInput.value = '';
        toggleAddChatForm();
        
        await loadChats();
        
        // Auto-expand the new chat
        setTimeout(() => {
            state.expandedChats.add(chatJid);
            displayChats(state.chats);
        }, 100);
        
    } catch (error) {
        console.error('Error adding chat:', error);
        showToast(`Failed to add chat: ${error.message}`, 'error');
    } finally {
        button.innerHTML = originalHtml;
            button.disabled = false;
    }
}

async function deleteChat(chatJid) {
    if (!confirm(`Are you sure you want to delete this chat?\n\n${chatJid}\n\nThis will stop all bots for this chat.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/chats/${encodeURIComponent(chatJid)}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete chat');
        }
        
        showToast('Chat deleted successfully', 'success');
        state.expandedChats.delete(chatJid);
        await loadChats();
        
    } catch (error) {
        console.error('Error deleting chat:', error);
        showToast(`Failed to delete chat: ${error.message}`, 'error');
    }
}

// ===================================
// BOT ACTIONS
// ===================================

async function toggleBotAssignment(botName, chatJid, enabled) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/chats/${encodeURIComponent(chatJid)}/bots/${encodeURIComponent(botName)}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled })
            }
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update assignment');
        }
        
        showToast(`Bot ${enabled ? 'enabled' : 'disabled'}`, 'success');
        
    } catch (error) {
        console.error('Error updating bot assignment:', error);
        showToast(`Failed to update: ${error.message}`, 'error');
        await loadChats();
    }
}

async function startBot(botName, chatJid) {
    const botCard = document.querySelector(`[data-bot-name="${botName}"][data-chat-jid="${chatJid}"]`);
    const startBtn = botCard?.querySelector('.bot-btn.start');
    
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.innerHTML = '<span class="loading-spinner"></span>';
    }
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/bots/${encodeURIComponent(botName)}/start?chat_jid=${encodeURIComponent(chatJid)}`,
            { method: 'POST' }
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start bot');
        }
        
        showToast(`Bot started: ${botName}`, 'success');
        await loadChats();
        
    } catch (error) {
        console.error(`Error starting bot ${botName}:`, error);
        showToast(`Failed to start bot: ${error.message}`, 'error');
    }
}

async function stopBot(botName, chatJid) {
    const botCard = document.querySelector(`[data-bot-name="${botName}"][data-chat-jid="${chatJid}"]`);
    const stopBtn = botCard?.querySelector('.bot-btn.stop');
    
    if (stopBtn) {
        stopBtn.disabled = true;
        stopBtn.innerHTML = '<span class="loading-spinner"></span>';
    }
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/bots/${encodeURIComponent(botName)}/stop?chat_jid=${encodeURIComponent(chatJid)}`,
            { method: 'POST' }
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to stop bot');
        }
        
        showToast(`Bot stopped: ${botName}`, 'success');
        
        const logsKey = `${botName}::${chatJid}`;
        state.expandedLogs.delete(logsKey);
        
        await loadChats();
        
    } catch (error) {
        console.error(`Error stopping bot ${botName}:`, error);
        showToast(`Failed to stop bot: ${error.message}`, 'error');
    }
}

async function toggleLogs(botName, chatJid) {
    const logsKey = `${botName}::${chatJid}`;
    const safeJid = makeSafeId(chatJid);
    const logsSection = document.getElementById(`logs-${botName}-${safeJid}`);
    
    if (!logsSection) {
        console.error(`Logs section not found for: ${botName} in ${chatJid}`);
        return;
    }
    
    if (logsSection.classList.contains('visible')) {
        logsSection.classList.remove('visible');
        state.expandedLogs.delete(logsKey);
    } else {
        logsSection.classList.add('visible');
        state.expandedLogs.add(logsKey);
        await loadBotLogs(botName, chatJid);
    }
}

async function loadBotLogs(botName, chatJid) {
    const safeJid = makeSafeId(chatJid);
    const container = document.getElementById(`logs-container-${botName}-${safeJid}`);
    
    if (!container) return;
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/bots/${encodeURIComponent(botName)}/logs?chat_jid=${encodeURIComponent(chatJid)}&limit=50`
        );
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayLogs(botName, chatJid, data.logs);
        
    } catch (error) {
        console.error(`Error loading logs for ${botName}:`, error);
        if (container) {
            container.innerHTML = `<p style="color: var(--danger);">Failed to load logs: ${error.message}</p>`;
        }
    }
}

function displayLogs(botName, chatJid, logs) {
    const safeJid = makeSafeId(chatJid);
    const container = document.getElementById(`logs-container-${botName}-${safeJid}`);
    
    if (!container) return;
    
    if (logs.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">No logs available</p>';
        return;
    }
    
    container.innerHTML = logs.map(log => `
        <div class="log-entry">
            <span class="log-timestamp">${formatTimestamp(log.timestamp)}</span>
            <span class="log-level ${log.level}">[${log.level}]</span>
            <span class="log-message">${escapeHtml(log.message)}</span>
        </div>
    `).join('');
}

// ===================================
// MESSAGES
// ===================================

async function toggleMessages(chatJid) {
    const safeJid = makeSafeId(chatJid);
    const messagesSection = document.getElementById(`messages-${safeJid}`);
    
    if (!messagesSection) return;
    
    if (messagesSection.classList.contains('visible')) {
        messagesSection.classList.remove('visible');
        state.expandedMessages.delete(chatJid);
    } else {
        messagesSection.classList.add('visible');
        state.expandedMessages.add(chatJid);
        await loadChatMessages(chatJid);
    }
}

async function loadChatMessages(chatJid) {
    const safeJid = makeSafeId(chatJid);
    const container = document.getElementById(`messages-container-${safeJid}`);
    
    if (!container) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/chats/${encodeURIComponent(chatJid)}/messages?limit=20`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayMessages(chatJid, data.results.messages);
        
    } catch (error) {
        console.error(`Error loading messages for ${chatJid}:`, error);
        if (container) {
            container.innerHTML = `<p style="color: var(--danger);">Failed to load messages: ${error.message}</p>`;
        }
    }
}

function displayMessages(chatJid, messages) {
    const safeJid = makeSafeId(chatJid);
    const container = document.getElementById(`messages-container-${safeJid}`);
    
    if (!container) return;
    
    if (messages.length === 0) {
        container.innerHTML = '<p style="color: var(--text-muted);">No messages available</p>';
        return;
    }
    
    container.innerHTML = messages.map(msg => {
        const timestamp = msg.timestamp ? formatRelativeTime(new Date(msg.timestamp)) : 'Unknown time';
        const sender = msg.sender_jid || msg.from || 'Unknown';
        const content = msg.content || msg.text || '[No text content]';
        const isFromMe = msg.is_from_me ? 'from-me' : 'from-them';
        
        return `
            <div class="message-bubble ${isFromMe}">
                ${!msg.is_from_me ? `<div class="message-sender">${escapeHtml(sender)}</div>` : ''}
                <div class="message-content">${escapeHtml(content)}</div>
                <div class="message-timestamp">${timestamp}</div>
            </div>
        `;
    }).join('');
}

// ===================================
// UTILITY FUNCTIONS
// ===================================

function makeSafeId(jid) {
    return jid.replace(/[@.:]/g, '-');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeAttr(text) {
    return text.replace(/'/g, "\\'");
}

function formatUptime(seconds) {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
}

function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString();
}

function formatRelativeTime(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
}

function filterChats() {
    displayChats(state.chats);
}

function displayBotsView() {
    const container = document.getElementById('chats-container');
    const sectionHeaderBar = document.querySelector('.section-header-bar');
    
    // Update section title
    const titleElement = sectionHeaderBar.querySelector('.section-title-large');
    if (titleElement) {
        titleElement.textContent = 'All Bots';
    }
    
    // Collect all bots from all chats
    const allBots = [];
    state.chats.forEach(chat => {
        chat.bots?.forEach(bot => {
            allBots.push({
                ...bot,
                chatJid: chat.chat_jid,
                chatName: chat.chat_name
            });
        });
    });
    
    // Filter by search query if present
    const filteredBots = state.searchQuery 
        ? allBots.filter(bot => 
            bot.display_name.toLowerCase().includes(state.searchQuery) ||
            bot.name.toLowerCase().includes(state.searchQuery) ||
            bot.chatName.toLowerCase().includes(state.searchQuery)
          )
        : allBots;
    
    if (filteredBots.length === 0) {
        if (state.searchQuery) {
            container.innerHTML = `
                <div class="empty-state glass-card" style="grid-column: 1 / -1;">
                    <div class="empty-icon">🔍</div>
                    <h3 class="empty-title">No bots found</h3>
                    <p class="empty-text">Try a different search term</p>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="empty-state glass-card" style="grid-column: 1 / -1;">
                    <div class="empty-icon">🤖</div>
                    <h3 class="empty-title">No Bots Available</h3>
                    <p class="empty-text">Add chats to see available bots</p>
                </div>
            `;
        }
    } else {
        // Display bots in a grid with chat context
        container.innerHTML = filteredBots.map(bot => createBotCardWithChat(bot)).join('');
    }
    
    document.getElementById('no-chats').style.display = 'none';
    container.style.display = 'grid';
}

function createBotCardWithChat(bot) {
    const isRunning = bot.status === 'running';
    const isEnabled = bot.enabled || false;
    const uptimeText = bot.uptime_seconds ? formatUptime(bot.uptime_seconds) : 'N/A';
    const logsKey = `${bot.name}::${bot.chatJid}`;
    const logsVisible = state.expandedLogs.has(logsKey);
    const safeJid = makeSafeId(bot.chatJid);
    const safeLogsId = `${bot.name}-${safeJid}`;
    const runningClass = isRunning ? 'running' : '';

    return `
        <div class="bot-card-standalone ${runningClass}" data-bot-name="${bot.name}" data-chat-jid="${bot.chatJid}">
            <div class="bot-chat-context">
                <span class="bot-chat-label">💬</span>
                <span class="bot-chat-name">${escapeHtml(bot.chatName)}</span>
            </div>
            
            <div class="bot-header">
                <div class="bot-name">${escapeHtml(bot.display_name)}</div>
                <div class="bot-status-badge ${bot.status}">${bot.status}</div>
            </div>
            
            <div class="bot-info">
                <div class="bot-info-row">
                    <span class="bot-info-label">Prefix</span>
                    <span class="bot-info-value">${escapeHtml(bot.prefix)}</span>
                </div>
                <div class="bot-info-row">
                    <span class="bot-info-label">Uptime</span>
                    <span class="bot-info-value">${uptimeText}</span>
                </div>
            </div>
            
            <div class="bot-toggle">
                <span class="bot-toggle-label">Enable Bot</span>
                <label class="toggle-switch">
                    <input type="checkbox" 
                           ${isEnabled ? 'checked' : ''} 
                           onchange="toggleBotAssignment('${bot.name}', '${escapeAttr(bot.chatJid)}', this.checked)">
                    <span class="toggle-slider"></span>
                </label>
            </div>
            
            <div class="bot-actions">
                <button class="bot-btn start" 
                        onclick="startBot('${bot.name}', '${escapeAttr(bot.chatJid)}')" 
                        ${isRunning ? 'disabled' : ''}>
                    ▶️
                </button>
                <button class="bot-btn stop" 
                        onclick="stopBot('${bot.name}', '${escapeAttr(bot.chatJid)}')" 
                        ${!isRunning ? 'disabled' : ''}>
                    ⏹️
                </button>
                <button class="bot-btn logs" 
                        onclick="toggleLogs('${bot.name}', '${escapeAttr(bot.chatJid)}')"
                        ${!isRunning ? 'disabled' : ''}>
                    📋
                </button>
            </div>
            
            <div class="logs-section ${logsVisible ? 'visible' : ''}" id="logs-${safeLogsId}">
                <div class="logs-container" id="logs-container-${safeLogsId}">
                    <p style="color: var(--text-muted);">Loading logs...</p>
                </div>
            </div>
        </div>
    `;
}

// ===================================
// STATE MANAGEMENT
// ===================================

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.querySelector('.error-message').textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    document.getElementById('error').style.display = 'none';
}

function showNoChats() {
    document.getElementById('no-chats').style.display = 'block';
    document.getElementById('chats-container').style.display = 'none';
}

// ===================================
// AUTO REFRESH
// ===================================

function startAutoRefresh() {
    if (state.refreshTimer) {
        clearInterval(state.refreshTimer);
    }
    
    state.refreshTimer = setInterval(async () => {
        await loadChatsQuietly();
    }, REFRESH_INTERVAL);
}

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', init);
