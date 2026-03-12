// ────────────────────────────────────────────────────────────
// Service Worker & PWA Install
// ────────────────────────────────────────────────────────────
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  document.getElementById('pwa-banner').classList.remove('hidden');
});

document.getElementById('pwa-install-btn')?.addEventListener('click', async () => {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      document.getElementById('pwa-banner').classList.add('hidden');
    }
    deferredPrompt = null;
  }
});

document.getElementById('pwa-dismiss-btn')?.addEventListener('click', () => {
  document.getElementById('pwa-banner').classList.add('hidden');
});

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(err => console.log('SW Registration failed: ', err));
  });
}

// ────────────────────────────────────────────────────────────
// Offline Detection
// ────────────────────────────────────────────────────────────
window.addEventListener('online', () => document.getElementById('offline-banner').classList.add('hidden'));
window.addEventListener('offline', () => document.getElementById('offline-banner').classList.remove('hidden'));

// ────────────────────────────────────────────────────────────
// Utilities
// ────────────────────────────────────────────────────────────
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideInRight 0.3s ease-in reverse forwards';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function getPosition() {
  return new Promise((resolve, reject) => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        err => resolve({ lat: 19.0760, lng: 72.8777 }) // Fallback Mumbai
      );
    } else {
      resolve({ lat: 19.0760, lng: 72.8777 });
    }
  });
}

function animateValue(obj, start, end, duration) {
  if (!obj) return;
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const current = progress * (end - start) + start;
    obj.innerHTML = current % 1 === 0 ? Math.floor(current) : current.toFixed(1);
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  };
  window.requestAnimationFrame(step);
}

// ────────────────────────────────────────────────────────────
// UI Updates
// ────────────────────────────────────────────────────────────
function updateRiskDisplay(level, score, data) {
  const badge = document.getElementById('risk-badge');
  const mainCard = document.getElementById('main-risk-card');
  const levelText = document.getElementById('risk-level-display');
  const descText = document.getElementById('risk-description');
  const alertBanner = document.getElementById('alert-banner');
  
  if (badge) {
    badge.className = `risk-badge ${level.toLowerCase()}`;
    badge.textContent = `${level} RISK`;
  }
  
  if (mainCard) {
    mainCard.className = `risk-card level-${level.toLowerCase()}`;
    if (levelText) levelText.textContent = `${level} RISK`;
    
    if (descText) {
      if (level === 'HIGH') descText.textContent = `CRITICAL: High flood risk detected due to ${data.rainfall_mm.toFixed(0)}mm rainfall and high soil saturation. Prepare for possible evacuation.`;
      else if (level === 'MEDIUM') descText.textContent = `WARNING: Conditions are degrading. Keep monitoring updates.`;
      else descText.textContent = `NORMAL: Current conditions are stable. No immediate threat detected.`;
    }
  }

  if (alertBanner) {
    if (level === 'HIGH') {
      alertBanner.textContent = '🚨 EMERGENCY: SEVERE FLOOD RISK DETECTED. PREPARE TO EVACUATE.';
      alertBanner.classList.remove('hidden');
      if (Notification.permission === 'granted') {
        new Notification('AquaAlert Emergency', { body: 'Severe flood risk detected in your area.', icon: '/static/icons/icon-192.png' });
      }
    } else {
      alertBanner.classList.add('hidden');
    }
  }
}

// ────────────────────────────────────────────────────────────
// Initialization
// ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Mobile menu
  const hamburger = document.getElementById('hamburgerBtn');
  const navLinks = document.querySelector('.nav-links');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      navLinks.classList.toggle('active');
    });
  }

  // Animate numbers
  document.querySelectorAll('.stat-num').forEach(el => {
    animateValue(el, 0, parseFloat(el.getAttribute('data-target')), 2000);
  });

  // Check offline status on load
  if (!navigator.onLine) {
    document.getElementById('offline-banner')?.classList.remove('hidden');
  }

  // Request notifications
  if ('Notification' in window && Notification.permission === 'default') {
    setTimeout(() => {
      Notification.requestPermission();
    }, 5000);
  }
});
