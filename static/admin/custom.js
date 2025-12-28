// Enhanced Admin Panel JavaScript

document.addEventListener("DOMContentLoaded", function () {
  // Initialize all enhancements
  initDashboardCharts();
  initFormEnhancements();
  initTableEnhancements();
  initSearchEnhancements();
  initLoadingStates();
  initTooltips();
});

// Dashboard Charts Initialization
function initDashboardCharts() {
  // This will be handled by the template's Chart.js code
  // Additional chart customizations can be added here
  console.log("Dashboard charts initialized");
}

// Form Enhancements
function initFormEnhancements() {
  // Add loading states to form submissions
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", function () {
      const submitBtn = form.querySelector(
        'input[type="submit"], button[type="submit"]'
      );
      if (submitBtn) {
        submitBtn.style.opacity = "0.7";
        submitBtn.style.pointerEvents = "none";

        // Add loading spinner
        const loading = document.createElement("span");
        loading.className = "loading";
        loading.style.marginLeft = "10px";
        submitBtn.appendChild(loading);
      }
    });
  });

  // Enhanced form validation
  const inputs = document.querySelectorAll("input, textarea, select");
  inputs.forEach((input) => {
    input.addEventListener("blur", function () {
      validateField(this);
    });

    input.addEventListener("input", function () {
      clearFieldError(this);
    });
  });
}

// Field Validation
function validateField(field) {
  const value = field.value.trim();
  const fieldType = field.type;
  const isRequired = field.hasAttribute("required");

  // Clear previous errors
  clearFieldError(field);

  // Required field validation
  if (isRequired && !value) {
    showFieldError(field, "This field is required");
    return false;
  }

  // Email validation
  if (fieldType === "email" && value) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      showFieldError(field, "Please enter a valid email address");
      return false;
    }
  }

  // Password validation
  if (fieldType === "password" && value) {
    if (value.length < 8) {
      showFieldError(field, "Password must be at least 8 characters long");
      return false;
    }
  }

  return true;
}

function showFieldError(field, message) {
  field.style.borderColor = "#ef4444";

  const errorDiv = document.createElement("div");
  errorDiv.className = "field-error";
  errorDiv.style.color = "#ef4444";
  errorDiv.style.fontSize = "0.875rem";
  errorDiv.style.marginTop = "5px";
  errorDiv.textContent = message;

  field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
  field.style.borderColor = "";
  const errorDiv = field.parentNode.querySelector(".field-error");
  if (errorDiv) {
    errorDiv.remove();
  }
}

// Table Enhancements
function initTableEnhancements() {
  // Add row selection functionality
  const tables = document.querySelectorAll("#changelist table");
  tables.forEach((table) => {
    addRowSelection(table);
    addSortableHeaders(table);
  });
}

function addRowSelection(table) {
  const rows = table.querySelectorAll("tbody tr");
  rows.forEach((row) => {
    row.addEventListener("click", function (e) {
      if (e.target.type !== "checkbox" && e.target.tagName !== "A") {
        const checkbox = row.querySelector('input[type="checkbox"]');
        if (checkbox) {
          checkbox.checked = !checkbox.checked;
          toggleRowSelection(row, checkbox.checked);
        }
      }
    });

    // Add hover effect
    row.addEventListener("mouseenter", function () {
      this.style.backgroundColor = "rgba(99, 102, 241, 0.05)";
    });

    row.addEventListener("mouseleave", function () {
      if (!this.querySelector('input[type="checkbox"]:checked')) {
        this.style.backgroundColor = "";
      }
    });
  });
}

function toggleRowSelection(row, isSelected) {
  if (isSelected) {
    row.style.backgroundColor = "rgba(99, 102, 241, 0.1)";
    row.classList.add("selected");
  } else {
    row.style.backgroundColor = "";
    row.classList.remove("selected");
  }
}

function addSortableHeaders(table) {
  const headers = table.querySelectorAll("thead th a");
  headers.forEach((header) => {
    header.addEventListener("click", function (e) {
      // Add loading state
      const tableContainer = table.closest("#changelist");
      if (tableContainer) {
        tableContainer.style.opacity = "0.7";
        tableContainer.style.pointerEvents = "none";
      }
    });
  });
}

// Search Enhancements
function initSearchEnhancements() {
  const searchInput = document.querySelector("#searchbar");
  if (searchInput) {
    // Add search suggestions
    searchInput.addEventListener(
      "input",
      debounce(function () {
        const query = this.value.trim();
        if (query.length > 2) {
          showSearchSuggestions(query);
        } else {
          hideSearchSuggestions();
        }
      }, 300)
    );

    // Add search icon
    const searchContainer = searchInput.parentNode;
    const searchIcon = document.createElement("span");
    searchIcon.innerHTML = "🔍";
    searchIcon.style.position = "absolute";
    searchIcon.style.right = "10px";
    searchIcon.style.top = "50%";
    searchIcon.style.transform = "translateY(-50%)";
    searchIcon.style.color = "#64748b";
    searchContainer.style.position = "relative";
    searchContainer.appendChild(searchIcon);
  }
}

function showSearchSuggestions(query) {
  // This would typically make an AJAX call to get suggestions
  // For now, we'll just show a placeholder
  console.log("Search suggestions for:", query);
}

function hideSearchSuggestions() {
  // Hide suggestions dropdown
  console.log("Hide search suggestions");
}

// Loading States
function initLoadingStates() {
  // Add loading states to action buttons
  const actionButtons = document.querySelectorAll(
    '.button, input[type="submit"]'
  );
  actionButtons.forEach((button) => {
    button.addEventListener("click", function () {
      if (this.type === "submit" || this.classList.contains("default")) {
        this.style.opacity = "0.7";
        this.style.pointerEvents = "none";

        const originalText = this.value || this.textContent;
        this.setAttribute("data-original-text", originalText);

        if (this.type === "submit") {
          this.value = "Processing...";
        } else {
          this.textContent = "Processing...";
        }
      }
    });
  });
}

// Tooltips
function initTooltips() {
  const tooltipElements = document.querySelectorAll("[title]");
  tooltipElements.forEach((element) => {
    element.addEventListener("mouseenter", showTooltip);
    element.addEventListener("mouseleave", hideTooltip);
  });
}

function showTooltip(e) {
  const element = e.target;
  const title = element.getAttribute("title");

  if (title) {
    const tooltip = document.createElement("div");
    tooltip.className = "custom-tooltip";
    tooltip.textContent = title;
    tooltip.style.cssText = `
            position: absolute;
            background: #1e293b;
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.875rem;
            z-index: 1000;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        `;

    document.body.appendChild(tooltip);

    const rect = element.getBoundingClientRect();
    tooltip.style.left =
      rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + "px";
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + "px";

    element.setAttribute("data-tooltip", "true");
    element.removeAttribute("title");
  }
}

function hideTooltip(e) {
  const element = e.target;
  const tooltip = document.querySelector(".custom-tooltip");

  if (tooltip) {
    tooltip.remove();
  }

  if (element.getAttribute("data-tooltip")) {
    // Restore original title if needed
    element.removeAttribute("data-tooltip");
  }
}

// Utility Functions
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// AJAX Enhancements
function makeAjaxRequest(url, options = {}) {
  const defaultOptions = {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRFToken(),
    },
  };

  const finalOptions = { ...defaultOptions, ...options };

  return fetch(url, finalOptions)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .catch((error) => {
      console.error("AJAX request failed:", error);
      showNotification("Request failed. Please try again.", "error");
    });
}

function getCSRFToken() {
  const token = document.querySelector("[name=csrfmiddlewaretoken]");
  return token ? token.value : "";
}

// Notification System
function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
    `;

  // Set background color based on type
  const colors = {
    success: "#10b981",
    error: "#ef4444",
    warning: "#f59e0b",
    info: "#6366f1",
  };
  notification.style.backgroundColor = colors[type] || colors.info;

  document.body.appendChild(notification);

  // Auto remove after 5 seconds
  setTimeout(() => {
    notification.style.animation = "slideOutRight 0.3s ease-in";
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }, 5000);
}

// Add CSS animations for notifications
const style = document.createElement("style");
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Export functions for global use
window.AdminEnhancements = {
  showNotification,
  makeAjaxRequest,
  validateField,
  clearFieldError,
};
