// ===================================
// MAGICAL PASSWORD PAGE SCRIPT
// ===================================

// Configuration
const API_BASE_URL = window.location.origin;

// Typing animation texts
const typingTexts = [
    "Welcome back, master! 🧙‍♂️",
    "Enter the secret realm... 🌟",
    "Your bots await you! 🤖",
    "Unlock the magic within... ✨"
];

let currentTextIndex = 0;
let currentCharIndex = 0;
let isDeleting = false;
let typingSpeed = 100;

// ===================================
// PARTICLE SYSTEM
// ===================================

class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.particleCount = 50;
        
        this.resize();
        this.init();
        
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    init() {
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                size: Math.random() * 3 + 1,
                speedX: (Math.random() - 0.5) * 0.5,
                speedY: (Math.random() - 0.5) * 0.5,
                opacity: Math.random() * 0.5 + 0.2
            });
        }
    }
    
    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles.forEach(particle => {
            // Create gradient for particle
            const gradient = this.ctx.createRadialGradient(
                particle.x, particle.y, 0,
                particle.x, particle.y, particle.size
            );
            gradient.addColorStop(0, `rgba(99, 102, 241, ${particle.opacity})`);
            gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');
            
            this.ctx.fillStyle = gradient;
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fill();
        });
    }
    
    update() {
        this.particles.forEach(particle => {
            particle.x += particle.speedX;
            particle.y += particle.speedY;
            
            // Wrap around screen
            if (particle.x < 0) particle.x = this.canvas.width;
            if (particle.x > this.canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = this.canvas.height;
            if (particle.y > this.canvas.height) particle.y = 0;
            
            // Pulsate opacity
            particle.opacity += (Math.random() - 0.5) * 0.02;
            particle.opacity = Math.max(0.1, Math.min(0.7, particle.opacity));
        });
    }
    
    animate() {
        this.update();
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
}

// ===================================
// TYPING ANIMATION
// ===================================

function typeText() {
    const typingElement = document.querySelector('.typing-text');
    const currentText = typingTexts[currentTextIndex];
    
    if (!isDeleting && currentCharIndex < currentText.length) {
        // Typing forward
        typingElement.textContent = currentText.substring(0, currentCharIndex + 1);
        currentCharIndex++;
        typingSpeed = 100;
    } else if (isDeleting && currentCharIndex > 0) {
        // Deleting
        typingElement.textContent = currentText.substring(0, currentCharIndex - 1);
        currentCharIndex--;
        typingSpeed = 50;
    } else {
        // Switch between typing and deleting
        isDeleting = !isDeleting;
        
        if (!isDeleting) {
            currentTextIndex = (currentTextIndex + 1) % typingTexts.length;
        }
        
        typingSpeed = 1000;
    }
    
    setTimeout(typeText, typingSpeed);
}

// ===================================
// PASSWORD TOGGLE
// ===================================

function setupPasswordToggle() {
    const toggleBtn = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('passwordInput');
    const eyeIcon = toggleBtn.querySelector('.eye-icon');
    
    toggleBtn.addEventListener('click', () => {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        
        // Toggle eye icon
        eyeIcon.textContent = type === 'password' ? '👁️' : '🙈';
        
        // Add bounce animation
        toggleBtn.style.transform = 'scale(1.2)';
        setTimeout(() => {
            toggleBtn.style.transform = 'scale(1)';
        }, 200);
    });
}

// ===================================
// FORM SUBMISSION
// ===================================

async function handleSubmit(event) {
    event.preventDefault();
    
    const form = document.getElementById('passwordForm');
    const passwordInput = document.getElementById('passwordInput');
    const submitBtn = form.querySelector('.submit-btn');
    const errorMessage = document.getElementById('errorMessage');
    const inputWrapper = document.querySelector('.input-wrapper');
    
    const password = passwordInput.value.trim();
    
    if (!password) {
        showError('Please enter a password');
        return;
    }
    
    // Hide error message
    errorMessage.classList.add('hidden');
    
    // Add loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    
    try {
        // Verify password with backend
        const response = await fetch(`${API_BASE_URL}/auth/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password })
        });
        
        if (response.ok) {
            // Success! Store auth token
            const data = await response.json();
            sessionStorage.setItem('auth_token', data.token || 'authenticated');
            
            // Success animation
            inputWrapper.classList.add('success-state');
            submitBtn.textContent = '✨ Welcome! ✨';
            
            // Check if there's a redirect URL
            const redirectUrl = sessionStorage.getItem('redirect_after_login') || 'index.html';
            sessionStorage.removeItem('redirect_after_login');
            
            // Redirect after animation
            setTimeout(() => {
                window.location.replace(redirectUrl);
            }, 1000);
        } else {
            // Wrong password
            throw new Error('Invalid password');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Invalid password. Try again!');
        
        // Shake animation
        passwordInput.value = '';
        inputWrapper.style.animation = 'shake 0.5s ease';
        setTimeout(() => {
            inputWrapper.style.animation = '';
        }, 500);
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
}

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    const errorText = errorMessage.querySelector('.error-text');
    
    errorText.textContent = message;
    errorMessage.classList.remove('hidden');
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        errorMessage.classList.add('hidden');
    }, 3000);
}

// ===================================
// INPUT EFFECTS
// ===================================

function setupInputEffects() {
    const passwordInput = document.getElementById('passwordInput');
    
    // Add sparkle effect on keypress
    passwordInput.addEventListener('keydown', (e) => {
        if (e.key.length === 1) {
            createSparkle(e.target);
        }
    });
    
    // Focus effects
    passwordInput.addEventListener('focus', () => {
        document.querySelector('.input-wrapper').style.transform = 'translateY(-2px)';
    });
    
    passwordInput.addEventListener('blur', () => {
        document.querySelector('.input-wrapper').style.transform = 'translateY(0)';
    });
}

function createSparkle(element) {
    const rect = element.getBoundingClientRect();
    const sparkle = document.createElement('div');
    
    sparkle.style.position = 'fixed';
    sparkle.style.left = rect.left + Math.random() * rect.width + 'px';
    sparkle.style.top = rect.top + rect.height / 2 + 'px';
    sparkle.style.fontSize = '12px';
    sparkle.textContent = '✨';
    sparkle.style.pointerEvents = 'none';
    sparkle.style.zIndex = '1000';
    sparkle.style.animation = 'sparkleFloat 1s ease-out forwards';
    
    document.body.appendChild(sparkle);
    
    setTimeout(() => sparkle.remove(), 1000);
}

// Add sparkle animation
const style = document.createElement('style');
style.textContent = `
    @keyframes sparkleFloat {
        0% {
            transform: translateY(0) scale(1);
            opacity: 1;
        }
        100% {
            transform: translateY(-50px) scale(0);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ===================================
// EASTER EGG - Konami Code
// ===================================

function setupKonamiCode() {
    const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    let konamiIndex = 0;
    
    document.addEventListener('keydown', (e) => {
        if (e.key === konamiCode[konamiIndex]) {
            konamiIndex++;
            if (konamiIndex === konamiCode.length) {
                activateEasterEgg();
                konamiIndex = 0;
            }
        } else {
            konamiIndex = 0;
        }
    });
}

function activateEasterEgg() {
    // Rainbow mode!
    const card = document.querySelector('.login-card');
    card.style.animation = 'rainbowBorder 2s linear infinite';
    
    // Add rainbow animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes rainbowBorder {
            0% { filter: hue-rotate(0deg); }
            100% { filter: hue-rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
    
    // Show message
    alert('🌈 Rainbow mode activated! 🌈');
}

// ===================================
// MOUSE TRAIL EFFECT
// ===================================

function setupMouseTrail() {
    const canvas = document.getElementById('particles');
    const ctx = canvas.getContext('2d');
    
    let mouseX = 0;
    let mouseY = 0;
    
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        
        // Create trail particle
        if (Math.random() > 0.8) {
            createTrailParticle(ctx, mouseX, mouseY);
        }
    });
}

function createTrailParticle(ctx, x, y) {
    const size = Math.random() * 5 + 2;
    const speedX = (Math.random() - 0.5) * 2;
    const speedY = (Math.random() - 0.5) * 2;
    let opacity = 1;
    
    function animate() {
        opacity -= 0.02;
        
        if (opacity <= 0) return;
        
        x += speedX;
        y += speedY;
        
        const gradient = ctx.createRadialGradient(x, y, 0, x, y, size);
        gradient.addColorStop(0, `rgba(139, 92, 246, ${opacity})`);
        gradient.addColorStop(1, 'rgba(139, 92, 246, 0)');
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fill();
        
        requestAnimationFrame(animate);
    }
    
    animate();
}

// ===================================
// INITIALIZATION
// ===================================

document.addEventListener('DOMContentLoaded', () => {
    // Check if already authenticated
    const authToken = sessionStorage.getItem('auth_token');
    if (authToken) {
        window.location.href = 'index.html';
        return;
    }
    
    // Initialize particle system
    const canvas = document.getElementById('particles');
    const particleSystem = new ParticleSystem(canvas);
    particleSystem.animate();
    
    // Start typing animation
    typeText();
    
    // Setup password toggle
    setupPasswordToggle();
    
    // Setup form submission
    const form = document.getElementById('passwordForm');
    form.addEventListener('submit', handleSubmit);
    
    // Setup input effects
    setupInputEffects();
    
    // Setup easter eggs
    setupKonamiCode();
    
    // Setup mouse trail
    setupMouseTrail();
    
    // Focus password input
    setTimeout(() => {
        document.getElementById('passwordInput').focus();
    }, 500);
});

