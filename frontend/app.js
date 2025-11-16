// ===================================
// MODERN WHATSAPP BOT DASHBOARD
// Enhanced with glassmorphism UI
// ===================================

const API_BASE_URL = window.location.origin;
const REFRESH_INTERVAL = 10000; // 10 seconds

// State management
const state = {
    chats: [],
    allChatsData: null, // Store the full API response with pagination info
    expandedChats: new Set(),
    expandedLogs: new Set(),
    expandedMessages: new Set(),
    expandedTableRows: new Set(),
    refreshTimer: null,
    currentView: 'dashboard',
    viewMode: 'cards', // 'cards' or 'table'
    searchQuery: '',
    
    // Table/Pagination state
    currentPage: 1,
    perPage: 20,
    sortBy: 'last_message_time',
    sortOrder: 'desc',
    
    // Filters
    filters: {
        activity: '',
        chatType: '',
        botStatus: '',
        search: ''
    },
    
    // Bulk selection
    selectedChats: new Set(),
    
    // Debounce timers
    searchDebounceTimer: null,
    filterDebounceTimer: null
};

// ===================================
// INITIALIZATION
// ===================================

async function init() {
    console.log('🚀 Initializing modern dashboard...');
    
    // Expose functions to global scope for inline onclick handlers
    window.startBot = startBot;
    window.stopBot = stopBot;
    window.toggleLogs = toggleLogs;
    window.toggleBotAssignment = toggleBotAssignment;
    window.toggleChat = toggleChat;
    window.toggleMessages = toggleMessages;
    window.deleteChat = deleteChat;
    
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

    // View toggle (table/cards)
    document.getElementById('tableViewBtn')?.addEventListener('click', () => switchViewMode('table'));
    document.getElementById('cardsViewBtn')?.addEventListener('click', () => switchViewMode('cards'));

    // Search with debouncing
    document.getElementById('searchChats')?.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        
        clearTimeout(state.searchDebounceTimer);
        state.searchDebounceTimer = setTimeout(() => {
            state.filters.search = query;
            state.searchQuery = query.toLowerCase();
            state.currentPage = 1; // Reset to first page on search
            
            if (state.viewMode === 'table') {
                loadChats();
            } else if (state.currentView === 'bots') {
                displayBotsView();
            } else {
                filterChats();
            }
        }, 300);
    });

    // Filters
    document.getElementById('activityFilter')?.addEventListener('change', (e) => {
        state.filters.activity = e.target.value;
        state.currentPage = 1;
        loadChats();
    });

    document.getElementById('chatTypeFilter')?.addEventListener('change', (e) => {
        state.filters.chatType = e.target.value;
        state.currentPage = 1;
        loadChats();
    });

    document.getElementById('botStatusFilter')?.addEventListener('change', (e) => {
        state.filters.botStatus = e.target.value;
        state.currentPage = 1;
        loadChats();
    });

    document.getElementById('clearFiltersBtn')?.addEventListener('click', clearFilters);

    // Pagination
    document.getElementById('firstPageBtn')?.addEventListener('click', () => goToPage(1));
    document.getElementById('prevPageBtn')?.addEventListener('click', () => goToPage(state.currentPage - 1));
    document.getElementById('nextPageBtn')?.addEventListener('click', () => goToPage(state.currentPage + 1));
    document.getElementById('lastPageBtn')?.addEventListener('click', () => {
        if (state.allChatsData) {
            goToPage(state.allChatsData.pagination.total_pages);
        }
    });

    document.getElementById('perPageSelect')?.addEventListener('change', (e) => {
        state.perPage = parseInt(e.target.value);
        state.currentPage = 1;
        loadChats();
    });

    // Select all checkbox
    document.getElementById('selectAllChats')?.addEventListener('change', (e) => {
        toggleSelectAll(e.target.checked);
    });

    // Bulk actions
    document.getElementById('bulkStartBots')?.addEventListener('click', () => bulkAction('start_bots'));
    document.getElementById('bulkStopBots')?.addEventListener('click', () => bulkAction('stop_bots'));
    document.getElementById('bulkDeleteChats')?.addEventListener('click', () => bulkAction('delete_chats'));
    document.getElementById('bulkCancelBtn')?.addEventListener('click', cancelBulkSelection);

    // Enter key on chat inputs
    document.getElementById('manualChatJid')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addChatManually();
    });
    document.getElementById('manualChatName')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addChatManually();
    });
    
    // Event delegation for bot action buttons (more reliable than inline onclick)
    document.addEventListener('click', (e) => {
        const target = e.target.closest('.bot-btn');
        if (!target) return;
        
        const botCard = target.closest('[data-bot-name][data-chat-jid]');
        if (!botCard) {
            console.error('Bot card not found for button:', target);
            return;
        }
        
        const botName = botCard.dataset.botName;
        const chatJid = botCard.dataset.chatJid;
        
        console.log('Bot button clicked:', { botName, chatJid, classList: target.classList.toString() });
        
        if (target.classList.contains('start')) {
            e.preventDefault();
            e.stopPropagation();
            startBot(botName, chatJid);
        } else if (target.classList.contains('stop')) {
            e.preventDefault();
            e.stopPropagation();
            stopBot(botName, chatJid);
        } else if (target.classList.contains('logs')) {
            e.preventDefault();
            e.stopPropagation();
            toggleLogs(botName, chatJid);
        }
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
        
        // Build query parameters
        const params = new URLSearchParams();
        
        if (state.viewMode === 'table') {
            params.append('page', state.currentPage);
            params.append('per_page', state.perPage);
            params.append('sort', state.sortBy);
            params.append('order', state.sortOrder);
            
            if (state.filters.activity) params.append('activity', state.filters.activity);
            if (state.filters.chatType) params.append('chat_type', state.filters.chatType);
            if (state.filters.botStatus) params.append('bot_status', state.filters.botStatus);
            if (state.filters.search) params.append('search', state.filters.search);
        }
        
        const response = await fetch(`${API_BASE_URL}/chats?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Handle both old format (array) and new format (object with pagination)
        if (Array.isArray(data)) {
            // Old format for backward compatibility
            state.chats = data;
            state.allChatsData = null;
        } else {
            // New paginated format
            state.chats = data.chats || [];
            state.allChatsData = data;
        }
        
        console.log('✓ Loaded chats:', state.chats.length);
        
        if (state.chats.length === 0 && !state.filters.search && !state.filters.activity) {
            showNoChats();
        } else {
            if (state.viewMode === 'table') {
                displayTableView();
            } else {
                displayChats(state.chats);
            }
        }
        
        updateDashboardStats();
        updateFilterInfo();
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
    console.log('startBot called:', { botName, chatJid });
    
    const botCard = document.querySelector(`[data-bot-name="${botName}"][data-chat-jid="${chatJid}"]`);
    const startBtn = botCard?.querySelector('.bot-btn.start');
    const originalHtml = startBtn?.innerHTML || '▶️';
    
    if (!botCard) {
        console.error('Bot card not found:', { botName, chatJid });
        showToast('Bot card not found', 'error');
        return;
    }
    
    if (startBtn) {
        startBtn.disabled = true;
        startBtn.innerHTML = '<span class="loading-spinner"></span>';
    }
    
    try {
        const url = `${API_BASE_URL}/bots/${encodeURIComponent(botName)}/start?chat_jid=${encodeURIComponent(chatJid)}`;
        console.log('Starting bot with URL:', url);
        
        const response = await fetch(url, { method: 'POST' });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || 'Failed to start bot');
        }
        
        showToast(`Bot started: ${botName}`, 'success');
        await loadChats();
        
    } catch (error) {
        console.error(`Error starting bot ${botName}:`, error);
        showToast(`Failed to start bot: ${error.message}`, 'error');
        
        // Reset button state on error
        if (startBtn) {
            startBtn.innerHTML = originalHtml;
            startBtn.disabled = false;
        }
    }
}

async function stopBot(botName, chatJid) {
    const botCard = document.querySelector(`[data-bot-name="${botName}"][data-chat-jid="${chatJid}"]`);
    const stopBtn = botCard?.querySelector('.bot-btn.stop');
    const originalHtml = stopBtn?.innerHTML || '⏹️';
    
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
        showToast(`Failed to start bot: ${error.message}`, 'error');
        
        // Reset button state on error
        if (stopBtn) {
            stopBtn.innerHTML = originalHtml;
            stopBtn.disabled = false;
        }
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
    // Escape for use in single-quoted JavaScript string within HTML attribute
    return text
        .replace(/\\/g, '\\\\')  // Escape backslashes first
        .replace(/'/g, "\\'")     // Escape single quotes
        .replace(/"/g, '\\"')     // Escape double quotes
        .replace(/\n/g, '\\n')    // Escape newlines
        .replace(/\r/g, '\\r');   // Escape carriage returns
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
// ERROR HANDLING
// ===================================

// Suppress Chrome extension errors that might interfere
window.addEventListener('error', (event) => {
    const message = event.message || '';
    // These are Chrome extension errors that don't affect functionality
    if (message.includes('chrome.runtime') || 
        message.includes('message channel closed') ||
        message.includes('Extension context invalidated')) {
        event.preventDefault();
        event.stopPropagation();
        console.debug('Suppressed Chrome extension error:', message);
        return false;
    }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    const message = event.reason?.message || String(event.reason);
    // Suppress Chrome extension promise rejections
    if (message.includes('chrome.runtime') || 
        message.includes('message channel closed') ||
        message.includes('Extension context invalidated')) {
        event.preventDefault();
        console.debug('Suppressed Chrome extension promise rejection:', message);
        return;
    }
    console.error('Unhandled promise rejection:', event.reason);
});

// ===================================
// VIEW MODE SWITCHING
// ===================================

function switchViewMode(mode) {
    state.viewMode = mode;
    
    // Update button states
    document.getElementById('tableViewBtn')?.classList.toggle('active', mode === 'table');
    document.getElementById('cardsViewBtn')?.classList.toggle('active', mode === 'cards');
    
    // Show/hide appropriate containers
    const tableContainer = document.getElementById('table-view-container');
    const cardsContainer = document.getElementById('chats-container');
    
    if (mode === 'table') {
        tableContainer.style.display = 'block';
        cardsContainer.style.display = 'none';
        loadChats();
    } else {
        tableContainer.style.display = 'none';
        cardsContainer.style.display = 'grid';
        displayChats(state.chats);
    }
    
    // Save preference
    localStorage.setItem('viewMode', mode);
}

// ===================================
// TABLE VIEW RENDERING
// ===================================

function displayTableView() {
    const tbody = document.getElementById('chatsTableBody');
    if (!tbody) return;
    
    if (state.chats.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-secondary);">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
                    <div style="font-size: 1.125rem; font-weight: 600;">No chats found</div>
                    <div style="font-size: 0.875rem; margin-top: 0.5rem;">Try adjusting your filters</div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = state.chats.map(chat => createTableRow(chat)).join('');
    renderPagination();
    updateBulkSelectionUI();
}

function createTableRow(chat) {
    const isSelected = state.selectedChats.has(chat.chat_jid);
    const isExpanded = state.expandedTableRows.has(chat.chat_jid);
    const runningBots = chat.bots.filter(b => b.status === 'running');
    const enabledBots = chat.bots.filter(b => b.enabled);
    
    // Activity status
    let activityBadge = '';
    let activityClass = 'idle';
    let activityText = 'Never';
    
    if (chat.last_message_time) {
        const lastMsg = new Date(chat.last_message_time);
        const now = new Date();
        const diffHours = (now - lastMsg) / (1000 * 60 * 60);
        
        if (diffHours < 24) {
            activityClass = 'active';
            activityText = formatRelativeTime(lastMsg);
        } else if (diffHours < 168) { // 7 days
            activityClass = 'recent';
            activityText = formatRelativeTime(lastMsg);
        } else {
            activityText = formatRelativeTime(lastMsg);
        }
        
        activityBadge = `<span class="activity-badge ${activityClass}">${activityClass.toUpperCase()}</span>`;
    }
    
    // Bot pills
    const botPills = chat.bots.slice(0, 3).map(bot => {
        const statusClass = bot.status === 'running' ? 'running' : (bot.enabled ? 'enabled' : '');
        const icon = bot.status === 'running' ? '▶️' : (bot.enabled ? '✓' : '○');
        return `<span class="bot-pill ${statusClass}"><span class="bot-pill-icon">${icon}</span>${escapeHtml(bot.display_name)}</span>`;
    }).join('');
    
    const moreBots = chat.bots.length > 3 ? `<span class="bot-pill">+${chat.bots.length - 3}</span>` : '';
    
    // Status badge
    let statusBadge = '';
    if (runningBots.length > 0) {
        statusBadge = `<span class="status-badge has-running">✓ ${runningBots.length} Running</span>`;
    } else if (enabledBots.length > 0) {
        statusBadge = `<span class="status-badge has-enabled">○ ${enabledBots.length} Enabled</span>`;
    } else {
        statusBadge = `<span class="status-badge no-bots">No Bots</span>`;
    }
    
    // Main row
    let html = `
        <tr class="${isSelected ? 'selected' : ''} ${isExpanded ? 'expanded' : ''}" data-chat-jid="${chat.chat_jid}">
            <td class="col-select">
                <input type="checkbox" class="chat-checkbox" 
                       ${isSelected ? 'checked' : ''} 
                       onchange="toggleChatSelection('${escapeAttr(chat.chat_jid)}', this.checked)">
            </td>
            <td class="col-name">
                <div class="chat-name-cell">
                    <div class="chat-name-primary">${escapeHtml(chat.chat_name)}</div>
                    <div class="chat-jid-secondary">${chat.chat_jid}</div>
                </div>
            </td>
            <td class="col-activity">
                <div class="activity-cell">
                    <div class="activity-time">${activityText}</div>
                    ${activityBadge}
                </div>
            </td>
            <td class="col-messages">
                <span class="message-count">${chat.message_count || 0}</span>
            </td>
            <td class="col-bots">
                <div class="bots-cell">
                    ${botPills}${moreBots}
                </div>
            </td>
            <td class="col-status">
                ${statusBadge}
            </td>
            <td class="col-actions">
                <div class="actions-cell">
                    <button class="table-action-btn expand" title="Expand" onclick="toggleTableRow('${escapeAttr(chat.chat_jid)}')">
                        ${isExpanded ? '▲' : '▼'}
                    </button>
                    <button class="table-action-btn" title="View Messages" onclick="toggleMessages('${escapeAttr(chat.chat_jid)}')">
                        💬
                    </button>
                    <button class="table-action-btn danger" title="Delete" onclick="deleteChat('${escapeAttr(chat.chat_jid)}')">
                        🗑️
                    </button>
                </div>
            </td>
        </tr>
    `;
    
    // Expanded details row
    if (isExpanded) {
        html += createExpandedRow(chat);
    }
    
    return html;
}

function createExpandedRow(chat) {
    const botsHtml = chat.bots.map(bot => {
        const isRunning = bot.status === 'running';
        const uptimeText = bot.uptime_seconds ? formatUptime(bot.uptime_seconds) : 'N/A';
        
        return `
            <div class="bot-detail-item">
                <div class="bot-detail-info">
                    <div class="bot-detail-name">${escapeHtml(bot.display_name)}</div>
                    <div class="bot-detail-meta">
                        Prefix: ${escapeHtml(bot.prefix)} | 
                        Uptime: ${uptimeText} | 
                        ${bot.enabled ? 'Enabled' : 'Disabled'}
                    </div>
                </div>
                <div class="bot-detail-actions">
                    <button class="bot-btn start" 
                            onclick="startBot('${bot.name}', '${escapeAttr(chat.chat_jid)}')" 
                            ${isRunning ? 'disabled' : ''}>
                        ▶️
                    </button>
                    <button class="bot-btn stop" 
                            onclick="stopBot('${bot.name}', '${escapeAttr(chat.chat_jid)}')" 
                            ${!isRunning ? 'disabled' : ''}>
                        ⏹️
                    </button>
                    <button class="bot-btn logs" 
                            onclick="toggleLogs('${bot.name}', '${escapeAttr(chat.chat_jid)}')"
                            ${!isRunning ? 'disabled' : ''}>
                        📋
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    return `
        <tr class="row-details">
            <td colspan="7">
                <div class="row-details-content">
                    <div class="details-section">
                        <div class="details-section-title">
                            <span>🤖</span> Bot Controls
                        </div>
                        <div class="bot-details-list">
                            ${botsHtml || '<p style="color: var(--text-secondary);">No bots available</p>'}
                        </div>
                    </div>
                    <div class="details-section">
                        <div class="details-section-title">
                            <span>💬</span> Recent Activity
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem;">
                            <p>Messages: ${chat.message_count || 0}</p>
                            <p>Last activity: ${chat.last_message_time ? formatRelativeTime(new Date(chat.last_message_time)) : 'Never'}</p>
                            <p>Added: ${formatRelativeTime(new Date(chat.added_at))}</p>
                        </div>
                    </div>
                </div>
            </td>
        </tr>
    `;
}

function toggleTableRow(chatJid) {
    if (state.expandedTableRows.has(chatJid)) {
        state.expandedTableRows.delete(chatJid);
    } else {
        state.expandedTableRows.add(chatJid);
    }
    displayTableView();
}

// ===================================
// PAGINATION
// ===================================

function renderPagination() {
    if (!state.allChatsData || !state.allChatsData.pagination) return;
    
    const { page, per_page, total, total_pages } = state.allChatsData.pagination;
    
    // Update info
    document.getElementById('paginationInfo').textContent = `Page ${page} of ${total_pages}`;
    
    // Update buttons
    document.getElementById('firstPageBtn').disabled = page === 1;
    document.getElementById('prevPageBtn').disabled = page === 1;
    document.getElementById('nextPageBtn').disabled = page === total_pages;
    document.getElementById('lastPageBtn').disabled = page === total_pages;
    
    // Render page numbers (show 5 at a time)
    const pageNumbers = document.getElementById('pageNumbers');
    const pages = [];
    
    let startPage = Math.max(1, page - 2);
    let endPage = Math.min(total_pages, page + 2);
    
    // Adjust if we're at the edges
    if (page <= 3) {
        endPage = Math.min(5, total_pages);
    } else if (page >= total_pages - 2) {
        startPage = Math.max(1, total_pages - 4);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        pages.push(`
            <button class="pagination-btn ${i === page ? 'active' : ''}" 
                    onclick="goToPage(${i})">
                ${i}
            </button>
        `);
    }
    
    pageNumbers.innerHTML = pages.join('');
}

function goToPage(page) {
    if (!state.allChatsData) return;
    
    const totalPages = state.allChatsData.pagination.total_pages;
    if (page < 1 || page > totalPages) return;
    
    state.currentPage = page;
    loadChats();
}

// ===================================
// FILTERING & SORTING
// ===================================

function clearFilters() {
    state.filters = {
        activity: '',
        chatType: '',
        botStatus: '',
        search: ''
    };
    state.currentPage = 1;
    
    document.getElementById('activityFilter').value = '';
    document.getElementById('chatTypeFilter').value = '';
    document.getElementById('botStatusFilter').value = '';
    document.getElementById('searchChats').value = '';
    
    loadChats();
}

function updateFilterInfo() {
    const showingCount = state.chats.length;
    const totalCount = state.allChatsData ? state.allChatsData.pagination.total : showingCount;
    
    document.getElementById('showingCount').textContent = showingCount;
    document.getElementById('totalCount').textContent = totalCount;
}

function handleSort(column) {
    if (state.sortBy === column) {
        // Toggle order
        state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        state.sortBy = column;
        state.sortOrder = 'desc';
    }
    
    // Update UI
    document.querySelectorAll('.chats-table th.sortable').forEach(th => {
        th.classList.remove('active-sort');
        const icon = th.querySelector('.sort-icon');
        if (icon) icon.textContent = '↕️';
    });
    
    const activeHeader = document.querySelector(`[data-sort="${column}"]`);
    if (activeHeader) {
        activeHeader.classList.add('active-sort');
        const icon = activeHeader.querySelector('.sort-icon');
        if (icon) icon.textContent = state.sortOrder === 'asc' ? '↑' : '↓';
    }
    
    state.currentPage = 1;
    loadChats();
}

// Add sorting event listeners
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.chats-table th.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const sortColumn = th.dataset.sort;
            if (sortColumn) handleSort(sortColumn);
        });
    });
});

// ===================================
// BULK ACTIONS
// ===================================

function toggleChatSelection(chatJid, checked) {
    if (checked) {
        state.selectedChats.add(chatJid);
    } else {
        state.selectedChats.delete(chatJid);
    }
    updateBulkSelectionUI();
}

function toggleSelectAll(checked) {
    if (checked) {
        state.chats.forEach(chat => state.selectedChats.add(chat.chat_jid));
    } else {
        state.selectedChats.clear();
    }
    displayTableView();
}

function updateBulkSelectionUI() {
    const count = state.selectedChats.size;
    const bulkBar = document.getElementById('bulkActionsBar');
    const selectAllCheckbox = document.getElementById('selectAllChats');
    
    if (count > 0) {
        bulkBar.style.display = 'flex';
        document.getElementById('selectedCount').textContent = count;
    } else {
        bulkBar.style.display = 'none';
    }
    
    // Update select all checkbox
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = state.chats.length > 0 && 
                                     state.chats.every(c => state.selectedChats.has(c.chat_jid));
    }
}

function cancelBulkSelection() {
    state.selectedChats.clear();
    displayTableView();
}

async function bulkAction(action) {
    const chatJids = Array.from(state.selectedChats);
    
    if (chatJids.length === 0) {
        showToast('No chats selected', 'warning');
        return;
    }
    
    // Confirmation for delete
    if (action === 'delete_chats') {
        if (!confirm(`Are you sure you want to delete ${chatJids.length} chat(s)?\n\nThis will stop all bots for these chats.`)) {
            return;
        }
    }
    
    showToast(`Processing ${chatJids.length} chat(s)...`, 'info');
    
    try {
        const response = await fetch(`${API_BASE_URL}/chats/bulk-action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_jids: chatJids,
                action: action
            })
        });
        
        if (!response.ok) {
            throw new Error('Bulk action failed');
        }
        
        const result = await response.json();
        
        const successCount = result.results.success.length;
        const failedCount = result.results.failed.length;
        
        if (failedCount > 0) {
            showToast(`Completed: ${successCount} succeeded, ${failedCount} failed`, 'warning');
        } else {
            showToast(`Successfully processed ${successCount} chat(s)`, 'success');
        }
        
        state.selectedChats.clear();
        await loadChats();
        
    } catch (error) {
        console.error('Bulk action error:', error);
        showToast(`Bulk action failed: ${error.message}`, 'error');
    }
}

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', init);
