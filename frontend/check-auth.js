// ===================================
// AUTHENTICATION CHECK FOR DASHBOARD
// This script protects all pages requiring authentication
// ===================================

(async function() {
    console.log('🔐 AUTH CHECK: Starting authentication check...');
    console.log('🔐 AUTH CHECK: Current page:', window.location.pathname);
    console.log('🔐 AUTH CHECK: Current URL:', window.location.href);
    
    const API_BASE_URL = window.location.origin;
    const currentPage = window.location.pathname;
    
    // Don't check auth on login page itself
    if (currentPage.includes('login.html')) {
        console.log('🔐 AUTH CHECK: On login page, skipping auth check');
        return;
    }
    
    // Show loading state while checking auth
    if (document.body) {
        document.body.style.opacity = '0';
        document.body.style.transition = 'opacity 0.3s ease';
    }
    
    // Check for auth token FIRST
    const authToken = sessionStorage.getItem('auth_token');
    console.log('🔐 AUTH CHECK: Token in sessionStorage:', authToken ? 'EXISTS' : 'MISSING');
    
    try {
        // Check if authentication is required
        console.log('🔐 AUTH CHECK: Fetching /auth/status...');
        const statusResponse = await fetch(`${API_BASE_URL}/auth/status`);
        console.log('🔐 AUTH CHECK: Status response:', statusResponse.status, statusResponse.ok);
        
        if (!statusResponse.ok) {
            // If auth endpoint fails, assume no auth required
            console.log('🔐 AUTH CHECK: Auth endpoint failed, assuming no authentication required');
            if (document.body) document.body.style.opacity = '1';
            return;
        }
        
        const statusData = await statusResponse.json();
        console.log('🔐 AUTH CHECK: Status data:', statusData);
        
        if (statusData.auth_required) {
            console.log('🔒 AUTH CHECK: Authentication IS REQUIRED for this dashboard');
            
            if (!authToken) {
                // Not authenticated - redirect to login immediately
                console.error('❌ AUTH CHECK: No auth token found - REDIRECTING TO LOGIN');
                sessionStorage.setItem('redirect_after_login', window.location.pathname);
                
                // Force redirect
                console.log('🔐 AUTH CHECK: Redirecting to login.html...');
                window.location.href = 'login.html';
                
                // Stop script execution
                throw new Error('Redirecting to login');
            }
            
            // Token exists - allow access
            console.log('✅ AUTH CHECK: User authenticated, access granted');
            if (document.body) document.body.style.opacity = '1';
            
            // Add logout functionality after DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', addLogoutButton);
            } else {
                // DOM already loaded
                addLogoutButton();
            }
        } else {
            // No authentication required
            console.log('🔓 AUTH CHECK: No authentication required');
            if (document.body) document.body.style.opacity = '1';
        }
    } catch (error) {
        console.error('❌ AUTH CHECK: Error during authentication check:', error);
        
        // On network error, check if we have a token
        if (!authToken) {
            // No token and can't check - redirect to login to be safe
            console.error('❌ AUTH CHECK: Network error and no token - REDIRECTING TO LOGIN');
            window.location.href = 'login.html';
            throw new Error('Redirecting to login');
        } else {
            // Has token but network error - allow access (fail open for UX)
            console.warn('⚠️ AUTH CHECK: Network error but has token - allowing access');
            if (document.body) document.body.style.opacity = '1';
            
            // Try to add logout button after DOM loads
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', addLogoutButton);
            } else {
                addLogoutButton();
            }
        }
    }
})();

// Add logout button to the sidebar
function addLogoutButton() {
    console.log('🔧 Attempting to add logout button...');
    
    // Check if logout button already exists
    if (document.getElementById('logoutBtn')) {
        console.log('✓ Logout button already exists');
        return;
    }
    
    // Find the sidebar footer
    const sidebarFooter = document.querySelector('.sidebar-footer');
    if (!sidebarFooter) {
        console.warn('⚠️ Sidebar footer not found, retrying in 500ms...');
        // Retry after a short delay
        setTimeout(addLogoutButton, 500);
        return;
    }
    
    console.log('✓ Sidebar footer found, creating logout button');
    
    // Create logout button
    const logoutBtn = document.createElement('button');
    logoutBtn.id = 'logoutBtn';
    logoutBtn.className = 'logout-btn';
    logoutBtn.innerHTML = `
        <span class="logout-icon">🚪</span>
        <span class="logout-text">Logout</span>
    `;
    
    // Add styles with explicit values (not CSS variables)
    const style = document.createElement('style');
    style.textContent = `
        .logout-btn {
            width: 100%;
            margin-top: 1rem;
            padding: 0.75rem 1rem;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 0.5rem;
            color: #ef4444;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            font-family: inherit;
        }
        
        .logout-btn:hover {
            background: rgba(239, 68, 68, 0.2);
            border-color: rgba(239, 68, 68, 0.5);
            transform: translateY(-2px);
        }
        
        .logout-btn:active {
            transform: translateY(0);
        }
        
        .logout-icon {
            font-size: 1.25rem;
        }
    `;
    document.head.appendChild(style);
    
    // Add click handler
    logoutBtn.addEventListener('click', handleLogout);
    
    // Add to sidebar
    sidebarFooter.appendChild(logoutBtn);
    
    console.log('✅ Logout button successfully added to sidebar');
}

// Handle logout
function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        console.log('🚪 Logging out...');
        
        // Clear session storage
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('redirect_after_login');
        
        // Show logout animation
        if (document.body) document.body.style.opacity = '0';
        
        // Redirect to login page after animation
        setTimeout(() => {
            window.location.replace('login.html');
        }, 300);
    }
}

// Expose functions globally so they can be called from other scripts
window.addLogoutButton = addLogoutButton;
window.handleLogout = handleLogout;

