document.addEventListener('DOMContentLoaded', () => {
  // 1. Navigation
  const hamburger = document.querySelector('.hamburger');
  const navMenu = document.querySelector('.nav-menu');
  
  if (hamburger) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('active');
      navMenu.classList.toggle('active');
    });
  }

  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
    
    // Smooth scroll for anchor links
    if (link.getAttribute('href').startsWith('#')) {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = link.getAttribute('href');
        if(targetId === '#') return;
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          targetElement.scrollIntoView({ behavior: 'smooth' });
          if(hamburger) hamburger.classList.remove('active');
          if(navMenu) navMenu.classList.remove('active');
        }
      });
    }
  });

  // 3. Stats counters on home page
  const statCounters = document.querySelectorAll('.stat-counter');
  if (statCounters.length > 0) {
    apiFetch('/api/stats').then(data => {
      if (data) {
        statCounters.forEach(counter => {
          const key = counter.dataset.stat;
          if (data[key]) {
            animateCounter(counter, data[key], 2000);
          }
        });
      }
    });
  }
});

// 2. Global utilities
const formatNumber = (n) => {
  return n.toLocaleString('en-IN');
};

const formatCurrency = (n) => {
  if (!n) return 'N/A';
  if (n >= 100000) {
    return `₹${(n / 100000).toFixed(2)}L`;
  }
  return `₹${n.toLocaleString('en-IN')}`;
};

const formatPackage = (lpa) => {
  if (!lpa) return 'N/A';
  return `₹${lpa} LPA`;
};

const classifyBadge = (classification) => {
  const colors = {
    'SAFE': 'badge-success',
    'MODERATE': 'badge-warning',
    'DREAM': 'badge-primary',
    'UNLIKELY': 'badge-danger'
  };
  const colorClass = colors[classification] || 'badge-secondary';
  return `<span class="badge ${colorClass}">${classification}</span>`;
};

const probabilityColor = (prob) => {
  if (prob >= 80) return '#28a745'; // Green
  if (prob >= 50) return '#ffc107'; // Yellow
  if (prob >= 20) return '#007bff'; // Blue
  return '#dc3545'; // Red
};

const trendIcon = (trend) => {
  if (trend > 0) return `<span style="color: #dc3545;">↗</span>`; // Cutoff increasing (harder)
  if (trend < 0) return `<span style="color: #28a745;">↘</span>`; // Cutoff decreasing (easier)
  return `<span style="color: #6c757d;">→</span>`;
};

const animateCounter = (element, target, duration) => {
  let start = 0;
  const increment = target / (duration / 16);
  const timer = setInterval(() => {
    start += increment;
    if (start >= target) {
      clearInterval(timer);
      element.innerText = formatNumber(target);
    } else {
      element.innerText = formatNumber(Math.floor(start));
    }
  }, 16);
};

// 4. Toast notification system
const showToast = (message, type = 'info') => {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px;';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const colors = {
    success: '#d4edda',
    error: '#f8d7da',
    info: '#cce5ff',
    warning: '#fff3cd'
  };
  const textColors = {
    success: '#155724',
    error: '#721c24',
    info: '#004085',
    warning: '#856404'
  };

  toast.style.cssText = `background-color: ${colors[type]}; color: ${textColors[type]}; padding: 15px 20px; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-width: 250px; font-family: sans-serif; opacity: 0; transition: opacity 0.3s ease-in-out;`;
  toast.innerHTML = `<strong>${type.toUpperCase()}:</strong> ${message}`;
  
  toastContainer.appendChild(toast);
  
  // Fade in
  setTimeout(() => { toast.style.opacity = '1'; }, 10);
  
  // Fade out and remove
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
};

const hideToast = () => {
  const toastContainer = document.getElementById('toast-container');
  if (toastContainer) toastContainer.innerHTML = '';
};

// 5. Generic Modal system
const showModal = (content, title = 'Modal') => {
  let modalContainer = document.getElementById('global-modal');
  if (!modalContainer) {
    modalContainer = document.createElement('div');
    modalContainer.id = 'global-modal';
    modalContainer.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 10000; opacity: 0; transition: opacity 0.3s;';
    
    const modalContent = document.createElement('div');
    modalContent.id = 'global-modal-content';
    modalContent.style.cssText = 'background: white; border-radius: 8px; width: 90%; max-width: 800px; max-height: 90vh; overflow-y: auto; padding: 20px; position: relative; transform: translateY(-20px); transition: transform 0.3s;';
    
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText = 'position: absolute; top: 15px; right: 20px; background: none; border: none; font-size: 24px; cursor: pointer;';
    closeBtn.onclick = hideModal;
    
    const titleEl = document.createElement('h3');
    titleEl.id = 'global-modal-title';
    titleEl.style.margin = '0 0 20px 0';
    
    const bodyEl = document.createElement('div');
    bodyEl.id = 'global-modal-body';
    
    modalContent.appendChild(closeBtn);
    modalContent.appendChild(titleEl);
    modalContent.appendChild(bodyEl);
    modalContainer.appendChild(modalContent);
    document.body.appendChild(modalContainer);
    
    // Close on backdrop click
    modalContainer.addEventListener('click', (e) => {
      if (e.target === modalContainer) hideModal();
    });
    
    // Close on Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') hideModal();
    });
  }
  
  document.getElementById('global-modal-title').innerText = title;
  document.getElementById('global-modal-body').innerHTML = content;
  
  modalContainer.style.display = 'flex';
  setTimeout(() => {
    modalContainer.style.opacity = '1';
    document.getElementById('global-modal-content').style.transform = 'translateY(0)';
  }, 10);
  
  document.body.style.overflow = 'hidden'; // prevent background scrolling
};

const hideModal = () => {
  const modalContainer = document.getElementById('global-modal');
  if (modalContainer) {
    modalContainer.style.opacity = '0';
    document.getElementById('global-modal-content').style.transform = 'translateY(-20px)';
    setTimeout(() => {
      modalContainer.style.display = 'none';
      document.body.style.overflow = 'auto';
    }, 300);
  }
};

// Global exports
window.formatNumber = formatNumber;
window.formatCurrency = formatCurrency;
window.formatPackage = formatPackage;
window.classifyBadge = classifyBadge;
window.probabilityColor = probabilityColor;
window.trendIcon = trendIcon;
window.animateCounter = animateCounter;
window.showToast = showToast;
window.hideToast = hideToast;
window.showModal = showModal;
window.hideModal = hideModal;
window.apiFetch = apiFetch;

// 6. Global error handler for fetch
const apiFetch = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    });
    
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(errText || `HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Fetch Error:', error);
    showToast('Failed to connect to server. Please try again.', 'error');
    throw error;
  }
};
