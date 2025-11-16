// ===================================
// AUTHENTICATION CHECK FOR DASHBOARD
// This script protects all pages requiring authentication
// ===================================

(async function() {
    const API_BASE_URL = window.location.origin;
    const currentPage = window.location.pathname;
    
    // Don't check auth on login page itself
    if (currentPage.includes('login.html')) {
        console.log('On login page, skipping auth check');
        return;
    }
    
    // Show loading state while checking auth
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.3s ease';
    
    try {
        // Check if authentication is required
        const statusResponse = await fetch(`${API_BASE_URL}/auth/status`);
        
        if (!statusResponse.ok) {
            // If auth endpoint fails, assume no auth required
            console.log('Auth check failed, assuming no authentication required');
            document.body.style.opacity = '1';
            return;
        }
        
        const statusData = await statusResponse.json();
        
        if (statusData.auth_required) {
            console.log('🔒 Authentication is REQUIRED for this dashboard');
            
            // Check if user has a valid token
            const authToken = sessionStorage.getItem('auth_token');
            
            if (!authToken) {
                // Not authenticated - redirect to login immediately
                console.log('❌ No auth token found, redirecting to login...');
                sessionStorage.setItem('redirect_after_login', window.location.pathname);
                window.location.replace('login.html');
                return;
            }
            
            // Verify the token is still valid (optional but recommended)
            console.log('✓ Auth token found, verifying...');
            
            // Token exists - allow access
            console.log('✅ User authenticated, access granted');
            document.body.style.opacity = '1';
            
            // Add logout functionality
            addLogoutButton();
        } else {
            // No authentication required
            console.log('🔓 No authentication required');
            document.body.style.opacity = '1';
        }
    } catch (error) {
        console.error('❌ Error checking authentication:', error);
        // On network error, check if we have a token
        const authToken = sessionStorage.getItem('auth_token');
        if (!authToken) {
            // No token and can't check - redirect to login to be safe
            console.log('Network error and no token - redirecting to login');
            window.location.replace('login.html');
        } else {
            // Has token but network error - allow access (fail open for UX)
            console.log('Network error but has token - allowing access');
            document.body.style.opacity = '1';
        }
    }
})();

// Add logout button to the sidebar
function addLogoutButton() {
    // Check if logout button already exists
    if (document.getElementById('logoutBtn')) {
        return;
    }
    
    // Find the sidebar footer
    const sidebarFooter = document.querySelector('.sidebar-footer');
    if (!sidebarFooter) {
        console.log('Sidebar footer not found, cannot add logout button');
        return;
    }
    
    // Create logout button
    const logoutBtn = document.createElement('button');
    logoutBtn.id = 'logoutBtn';
    logoutBtn.className = 'logout-btn';
    logoutBtn.innerHTML = `
        <span class="logout-icon">🚪</span>
        <span class="logout-text">Logout</span>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .logout-btn {
            width: 100%;
            margin-top: var(--spacing-md);
            padding: var(--spacing-md) var(--spacing-lg);
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: var(--radius-md);
            color: #ef4444;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all var(--transition-base);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: var(--spacing-sm);
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
    
    console.log('✓ Logout button added to sidebar');
}

// Handle logout
function handleLogout() {
    if (confirm('Are you sure you want to logout?')) {
        console.log('🚪 Logging out...');
        
        // Clear session storage
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('redirect_after_login');
        
        // Show logout animation
        document.body.style.opacity = '0';
        
        // Redirect to login page after animation
        setTimeout(() => {
            window.location.replace('login.html');
        }, 300);
    }
}

