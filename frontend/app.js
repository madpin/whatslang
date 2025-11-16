// Frontend logic for multi-chat bot dashboard

const API_BASE_URL = window.location.origin;
const REFRESH_INTERVAL = 10000; // 10 seconds

let refreshTimer = null;
let expandedChats = new Set();
let expandedLogs = new Set();
let expandedMessages = new Set();

// Helper function to create safe IDs from JIDs
function makeSafeId(jid) {
    return jid.replace(/[@.:]/g, '-');
}

// Initialize the dashboard
async function init() {
    console.log('Initializing multi-chat dashboard...');
    
    // Set up event listeners
    document.getElementById('syncChatsBtn').addEventListener('click', syncChats);
    document.getElementById('addChatBtn').addEventListener('click', addChatManually);
    
    await loadChats();
    startAutoRefresh();
}

// Load and display all chats
async function loadChats() {
    try {
        const response = await fetch(`${API_BASE_URL}/chats`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const chats = await response.json();
        console.log('Loaded chats:', chats);
        
        if (chats.length === 0) {
            showNoChats();
        } else {
            // Expand all chats by default if no chats were previously expanded
            if (expandedChats.size === 0) {
                chats.forEach(chat => expandedChats.add(chat.chat_jid));
            }
            displayChats(chats);
        }
        
        hideLoading();
        hideError();
    } catch (error) {
        console.error('Error loading chats:', error);
        showError('Failed to load chats: ' + error.message);
        hideLoading();
    }
}

// Display chats in sections
function displayChats(chats) {
    const container = document.getElementById('chats-container');
    container.innerHTML = chats.map(chat => createChatSection(chat)).join('');
    
    // Re-expand previously expanded chats and logs
    expandedChats.forEach(chatJid => {
        const chatElement = document.querySelector(`[data-chat-jid="${chatJid}"]`);
        if (chatElement) {
            chatElement.classList.add('expanded');
        }
    });
    
    // Refresh logs for expanded bots
    for (const key of expandedLogs) {
        const [botName, chatJid] = key.split('::');
        loadBotLogs(botName, chatJid);
    }
    
    document.getElementById('no-chats').style.display = 'none';
    container.style.display = 'flex';
}

// Create HTML for a chat section
function createChatSection(chat) {
    const isExpanded = expandedChats.has(chat.chat_jid);
    const expandedClass = isExpanded ? 'expanded' : '';
    const enabledCount = chat.bots.filter(b => b.enabled).length;
    const runningCount = chat.bots.filter(b => b.status === 'running').length;
    
    let botsContent = '';
    if (chat.bots && chat.bots.length > 0) {
        botsContent = chat.bots.map(bot => createBotCard(bot, chat.chat_jid)).join('');
    } else {
        botsContent = `
            <div class="bots-grid-empty">
                <p>No bots discovered yet</p>
                <p style="font-size: 0.9rem; margin-top: 8px; color: #9ca3af;">Bots will appear here automatically when the bot service discovers them.</p>
            </div>
        `;
    }
    
    const messagesVisible = expandedMessages.has(chat.chat_jid);
    const safeJid = makeSafeId(chat.chat_jid);
    
    return `
        <div class="chat-section ${expandedClass}" data-chat-jid="${chat.chat_jid}">
            <div class="messages-section ${messagesVisible ? 'visible' : ''}" id="messages-${safeJid}">
                <div class="messages-header">
                    <span class="messages-title">Recent Messages</span>
                    <button onclick="event.stopPropagation(); toggleMessages('${chat.chat_jid}')" style="background: none; border: none; color: #374151; cursor: pointer; font-size: 1.2rem;">×</button>
                </div>
                <div class="messages-container" id="messages-container-${safeJid}">
                    <p style="color: #9ca3af;">Loading messages...</p>
                </div>
            </div>
            <div class="chat-header" onclick="toggleChat('${chat.chat_jid}')">
                <div class="chat-info">
                    <h2>${escapeHtml(chat.chat_name)}</h2>
                    <div class="chat-jid">${chat.chat_jid}</div>
                    ${chat.bots.length > 0 ? `
                        <div style="margin-top: 8px; font-size: 0.875rem; opacity: 0.9;">
                            ${enabledCount} enabled • ${runningCount} running • ${chat.bots.length} total
                        </div>
                    ` : ''}
                </div>
                <div class="chat-controls">
                    <button class="btn-logs" onclick="event.stopPropagation(); toggleMessages('${chat.chat_jid}')" title="View recent messages">
                        💬 Messages
                    </button>
                    <button class="btn-delete" onclick="event.stopPropagation(); deleteChat('${chat.chat_jid}')" title="Delete this chat">
                        🗑️ Delete
                    </button>
                    <span class="expand-icon">▼</span>
                </div>
            </div>
            <div class="bots-grid">
                ${botsContent}
            </div>
        </div>
    `;
}

// Create HTML for a bot card
function createBotCard(bot, chatJid) {
    const isRunning = bot.status === 'running';
    const isEnabled = bot.enabled || false;
    const uptimeText = bot.uptime_seconds 
        ? formatUptime(bot.uptime_seconds) 
        : 'N/A';
    const logsKey = `${bot.name}::${chatJid}`;
    const logsVisible = expandedLogs.has(logsKey);
    const safeJid = makeSafeId(chatJid);
    const safeLogsId = `${bot.name}-${safeJid}`;
    
    return `
        <div class="bot-card" data-bot-name="${bot.name}" data-chat-jid="${chatJid}">
            <div class="bot-header-section">
                <span class="bot-name">${bot.display_name}</span>
                <span class="bot-status ${bot.status}">${bot.status}</span>
            </div>
            
            <div class="bot-info">
                <div class="bot-info-item">
                    <span class="bot-info-label">Prefix:</span>
                    <span>${bot.prefix}</span>
                </div>
                <div class="bot-info-item">
                    <span class="bot-info-label">Uptime:</span>
                    <span>${uptimeText}</span>
                </div>
            </div>
            
            <div class="toggle-container">
                <span class="toggle-label">Enable Bot</span>
                <label class="toggle-switch">
                    <input type="checkbox" 
                           ${isEnabled ? 'checked' : ''} 
                           onchange="toggleBotAssignment('${bot.name}', '${escapeHtml(chatJid)}', this.checked)">
                    <span class="toggle-slider"></span>
                </label>
            </div>
            
            <div class="bot-actions">
                <button class="btn-start" 
                        onclick="startBot('${bot.name}', '${escapeHtml(chatJid)}')" 
                        ${isRunning ? 'disabled' : ''}>
                    ▶️ Start
                </button>
                <button class="btn-stop" 
                        onclick="stopBot('${bot.name}', '${escapeHtml(chatJid)}')" 
                        ${!isRunning ? 'disabled' : ''}>
                    ⏹️ Stop
                </button>
                <button class="btn-logs" 
                        onclick="toggleLogs('${bot.name}', '${escapeHtml(chatJid)}')"
                        ${!isRunning ? 'disabled' : ''}>
                    📋 Logs
                </button>
            </div>
            
            <div class="logs-section ${logsVisible ? 'visible' : ''}" id="logs-${safeLogsId}">
                <div class="logs-header">
                    <span class="logs-title">Recent Logs</span>
                </div>
                <div class="logs-container" id="logs-container-${safeLogsId}">
                    <p style="color: #9ca3af;">Loading logs...</p>
                </div>
            </div>
        </div>
    `;
}

// Toggle chat expansion
function toggleChat(chatJid) {
    const chatElement = document.querySelector(`[data-chat-jid="${chatJid}"]`);
    
    if (chatElement.classList.contains('expanded')) {
        chatElement.classList.remove('expanded');
        expandedChats.delete(chatJid);
    } else {
        chatElement.classList.add('expanded');
        expandedChats.add(chatJid);
    }
}

// Sync chats from WhatsApp API
async function syncChats() {
    const button = document.getElementById('syncChatsBtn');
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span style="display: inline-block; animation: spin 1s linear infinite;">🔄</span> Syncing...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/chats/sync`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to sync chats');
        }
        
        const result = await response.json();
        console.log('Sync result:', result.message);
        
        // Show success feedback
        button.innerHTML = '✅ ' + result.message;
        button.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        
        // Reload chats
        await loadChats();
        
        // Reset button after 2 seconds
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = '';
            button.disabled = false;
        }, 2000);
    } catch (error) {
        console.error('Error syncing chats:', error);
        button.innerHTML = '❌ Sync Failed';
        button.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
        
        showError(`Failed to sync chats: ${error.message}`);
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = '';
            button.disabled = false;
        }, 3000);
    }
}

// Add chat manually
async function addChatManually() {
    const chatJidInput = document.getElementById('manualChatJid');
    const chatNameInput = document.getElementById('manualChatName');
    const button = document.getElementById('addChatBtn');
    
    const chatJid = chatJidInput.value.trim();
    const chatName = chatNameInput.value.trim();
    
    if (!chatJid) {
        chatJidInput.style.borderColor = '#ef4444';
        chatJidInput.focus();
        setTimeout(() => {
            chatJidInput.style.borderColor = '';
        }, 2000);
        return;
    }
    
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '➕ Adding...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/chats`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                chat_jid: chatJid,
                chat_name: chatName || null
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add chat');
        }
        
        console.log('Chat added successfully');
        
        // Show success feedback
        button.innerHTML = '✅ Added!';
        button.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
        
        // Clear form
        chatJidInput.value = '';
        chatNameInput.value = '';
        
        // Reload chats
        await loadChats();
        
        // Auto-expand the new chat
        setTimeout(() => {
            expandedChats.add(chatJid);
            loadChats();
        }, 100);
        
        // Reset button
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = '';
            button.disabled = false;
        }, 2000);
    } catch (error) {
        console.error('Error adding chat:', error);
        button.innerHTML = '❌ Failed';
        button.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
        
        showError(`Failed to add chat: ${error.message}`);
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.style.background = '';
            button.disabled = false;
        }, 3000);
    }
}

// Delete chat
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
        
        console.log('Chat deleted successfully');
        
        // Remove from expanded sets
        expandedChats.delete(chatJid);
        
        // Reload chats
        await loadChats();
    } catch (error) {
        console.error('Error deleting chat:', error);
        alert(`Failed to delete chat: ${error.message}`);
    }
}

// Toggle bot assignment (enable/disable)
async function toggleBotAssignment(botName, chatJid, enabled) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/chats/${encodeURIComponent(chatJid)}/bots/${encodeURIComponent(botName)}`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ enabled })
            }
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update assignment');
        }
        
        console.log(`Bot ${botName} ${enabled ? 'enabled' : 'disabled'} for chat ${chatJid}`);
    } catch (error) {
        console.error('Error updating bot assignment:', error);
        alert(`Failed to update bot assignment: ${error.message}`);
        // Reload to reset the toggle
        await loadChats();
    }
}

// Start a bot
async function startBot(botName, chatJid) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/bots/${encodeURIComponent(botName)}/start?chat_jid=${encodeURIComponent(chatJid)}`,
            {
                method: 'POST'
            }
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to start bot');
        }
        
        console.log(`Started bot: ${botName} for chat ${chatJid}`);
        await loadChats(); // Refresh the display
    } catch (error) {
        console.error(`Error starting bot ${botName}:`, error);
        alert(`Failed to start bot: ${error.message}`);
    }
}

// Stop a bot
async function stopBot(botName, chatJid) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/bots/${encodeURIComponent(botName)}/stop?chat_jid=${encodeURIComponent(chatJid)}`,
            {
                method: 'POST'
            }
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to stop bot');
        }
        
        console.log(`Stopped bot: ${botName} for chat ${chatJid}`);
        
        const logsKey = `${botName}::${chatJid}`;
        expandedLogs.delete(logsKey); // Remove from expanded logs
        
        await loadChats(); // Refresh the display
    } catch (error) {
        console.error(`Error stopping bot ${botName}:`, error);
        alert(`Failed to stop bot: ${error.message}`);
    }
}

// Toggle logs visibility
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
        expandedLogs.delete(logsKey);
    } else {
        logsSection.classList.add('visible');
        expandedLogs.add(logsKey);
        await loadBotLogs(botName, chatJid);
    }
}

// Load logs for a bot
async function loadBotLogs(botName, chatJid) {
    const safeJid = makeSafeId(chatJid);
    
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
        const container = document.getElementById(`logs-container-${botName}-${safeJid}`);
        if (container) {
            container.innerHTML = `<p style="color: #f87171;">Failed to load logs: ${error.message}</p>`;
        }
    }
}

// Display logs in the container
function displayLogs(botName, chatJid, logs) {
    const safeJid = makeSafeId(chatJid);
    const container = document.getElementById(`logs-container-${botName}-${safeJid}`);
    
    if (!container) {
        console.error(`Logs container not found for: ${botName} in ${chatJid}`);
        return;
    }
    
    if (logs.length === 0) {
        container.innerHTML = '<p style="color: #9ca3af;">No logs available</p>';
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

// Format uptime in human-readable format
function formatUptime(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        return `${minutes}m`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

// Format timestamp
function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString();
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start auto-refresh
function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    
    refreshTimer = setInterval(async () => {
        await loadChatsQuietly();
    }, REFRESH_INTERVAL);
}

// Load chats without visual disruption (for auto-refresh)
async function loadChatsQuietly() {
    try {
        const response = await fetch(`${API_BASE_URL}/chats`);
        if (!response.ok) {
            return; // Silently fail on auto-refresh
        }
        
        const chats = await response.json();
        
        // Only update if there are changes
        const currentChatIds = Array.from(document.querySelectorAll('.chat-section')).map(
            el => el.dataset.chatJid
        );
        const newChatIds = chats.map(c => c.chat_jid);
        
        // Check if chat list changed (added/removed chats)
        const chatsChanged = JSON.stringify(currentChatIds.sort()) !== JSON.stringify(newChatIds.sort());
        
        if (chatsChanged) {
            // Full reload if chats added/removed
            displayChats(chats);
        } else {
            // Just update bot statuses without full reload
            updateBotStatuses(chats);
        }
    } catch (error) {
        console.debug('Auto-refresh failed:', error);
        // Silently fail - don't disrupt the user
    }
}

// Update bot statuses without full DOM rebuild
function updateBotStatuses(chats) {
    chats.forEach(chat => {
        const chatElement = document.querySelector(`[data-chat-jid="${chat.chat_jid}"]`);
        if (!chatElement) return;
        
        // Update stats in header
        const enabledCount = chat.bots.filter(b => b.enabled).length;
        const runningCount = chat.bots.filter(b => b.status === 'running').length;
        
        chat.bots.forEach(bot => {
            const botCard = chatElement.querySelector(`[data-bot-name="${bot.name}"]`);
            if (!botCard) return;
            
            // Update status badge
            const statusBadge = botCard.querySelector('.bot-status');
            if (statusBadge) {
                statusBadge.className = `bot-status ${bot.status}`;
                statusBadge.textContent = bot.status;
            }
            
            // Update uptime
            const uptimeElements = botCard.querySelectorAll('.bot-info-item');
            uptimeElements.forEach(item => {
                const label = item.querySelector('.bot-info-label');
                if (label && label.textContent === 'Uptime:') {
                    const valueSpan = item.querySelector('span:last-child');
                    if (valueSpan) {
                        valueSpan.textContent = bot.uptime_seconds ? formatUptime(bot.uptime_seconds) : 'N/A';
                    }
                }
            });
            
            // Update buttons state
            const isRunning = bot.status === 'running';
            const startBtn = botCard.querySelector('.btn-start');
            const stopBtn = botCard.querySelector('.btn-stop');
            const logsBtn = botCard.querySelector('.btn-logs');
            
            if (startBtn) startBtn.disabled = isRunning;
            if (stopBtn) stopBtn.disabled = !isRunning;
            if (logsBtn) logsBtn.disabled = !isRunning;
            
            // Update toggle if needed
            const toggle = botCard.querySelector('.toggle-switch input');
            if (toggle && toggle.checked !== bot.enabled) {
                toggle.checked = bot.enabled;
            }
        });
    });
}

// Show/hide states
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.querySelector('p').textContent = message;
    errorDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideError();
    }, 5000);
}

function hideError() {
    document.getElementById('error').style.display = 'none';
}

function showNoChats() {
    document.getElementById('no-chats').style.display = 'block';
    document.getElementById('chats-container').style.display = 'none';
}

// Toggle messages visibility
async function toggleMessages(chatJid) {
    const safeJid = makeSafeId(chatJid);
    const messagesSection = document.getElementById(`messages-${safeJid}`);
    
    if (!messagesSection) {
        console.error(`Messages section not found for: ${chatJid}`);
        return;
    }
    
    if (messagesSection.classList.contains('visible')) {
        messagesSection.classList.remove('visible');
        expandedMessages.delete(chatJid);
    } else {
        messagesSection.classList.add('visible');
        expandedMessages.add(chatJid);
        await loadChatMessages(chatJid);
    }
}

// Load messages for a chat
async function loadChatMessages(chatJid) {
    const safeJid = makeSafeId(chatJid);
    
    try {
        const response = await fetch(`${API_BASE_URL}/chats/${encodeURIComponent(chatJid)}/messages?limit=20`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayMessages(chatJid, data.results.messages);
    } catch (error) {
        console.error(`Error loading messages for ${chatJid}:`, error);
        const container = document.getElementById(`messages-container-${safeJid}`);
        if (container) {
            container.innerHTML = `<p style="color: #f87171;">Failed to load messages: ${error.message}</p>`;
        }
    }
}

// Display messages in the container
function displayMessages(chatJid, messages) {
    const safeJid = makeSafeId(chatJid);
    const container = document.getElementById(`messages-container-${safeJid}`);
    
    if (!container) {
        console.error(`Messages container not found for: ${chatJid}`);
        return;
    }
    
    if (messages.length === 0) {
        container.innerHTML = '<p style="color: #9ca3af;">No messages available</p>';
        return;
    }
    
    container.innerHTML = messages.map(msg => {
        const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleString() : 'Unknown time';
        const sender = msg.sender_jid || msg.from || 'Unknown';
        const content = msg.content || msg.text || '[No text content]';
        const isFromMe = msg.is_from_me ? 'from-me' : 'from-them';
        
        return `
            <div class="message-entry ${isFromMe}">
                <div class="message-header">
                    <span class="message-sender">${escapeHtml(sender)}</span>
                    <span class="message-timestamp">${timestamp}</span>
                </div>
                <div class="message-content">${escapeHtml(content)}</div>
            </div>
        `;
    }).join('');
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', init);
