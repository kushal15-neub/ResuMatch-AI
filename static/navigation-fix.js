// Navigation fix to prevent back button reload issues
(function () {
  "use strict";

  // Track navigation state
  let navigationState = {
    isNavigating: false,
    currentPage: window.location.pathname,
    historyLength: window.history.length,
    isAuthenticated: false,
  };

  // Check authentication status from server response
  function checkAuthenticationStatus() {
    // Check if user is authenticated by looking for auth indicators
    const authIndicators = [
      document.querySelector(".user-welcome"),
      document.querySelector('a[href*="logout"]'),
      document.querySelector('.nav-link:contains("Welcome")'),
    ];

    navigationState.isAuthenticated = authIndicators.some(
      (indicator) => indicator !== null
    );

    // Also check for authentication status in meta tag or data attribute
    const authMeta = document.querySelector('meta[name="auth-status"]');
    if (authMeta) {
      navigationState.isAuthenticated = authMeta.content === "authenticated";
    }
  }

  // Override browser back/forward behavior
  function handleNavigation() {
    // Prevent page reload on back button
    window.addEventListener("popstate", function (event) {
      if (navigationState.isNavigating) {
        return;
      }

      navigationState.isNavigating = true;

      // Get the target URL from history state or construct it
      let targetUrl = event.state ? event.state.url : document.referrer;

      if (!targetUrl || targetUrl === window.location.href) {
        // If no valid target, go to home page
        targetUrl = "/";
      }

      // Check if user is trying to navigate to auth pages when authenticated
      const authPages = [
        "/login/",
        "/register/",
        "/forgot-password/",
        "/reset-password/",
      ];
      const isAuthPage = authPages.some((page) => targetUrl.includes(page));

      if (navigationState.isAuthenticated && isAuthPage) {
        // Redirect authenticated users to CV templates instead of auth pages
        targetUrl = "/cv-templates/";
      }

      // Use proper navigation instead of reload
      if (targetUrl !== window.location.pathname) {
        window.location.href = targetUrl;
      } else {
        navigationState.isNavigating = false;
      }
    });

    // Override browser back button behavior
    window.addEventListener("beforeunload", function (event) {
      // Store current state for back button handling
      if (window.history && window.history.replaceState) {
        window.history.replaceState(
          {
            url: window.location.pathname,
            timestamp: Date.now(),
            isAuthenticated: navigationState.isAuthenticated,
          },
          "",
          window.location.pathname
        );
      }
    });
  }

  // Fix form submissions to use proper navigation
  function fixFormNavigation() {
    const forms = document.querySelectorAll("form");
    forms.forEach((form) => {
      form.addEventListener("submit", function (e) {
        // Let the form submit normally, but track it
        navigationState.isNavigating = true;

        // Reset navigation state after a delay
        setTimeout(() => {
          navigationState.isNavigating = false;
        }, 1000);
      });
    });
  }

  // Fix link navigation
  function fixLinkNavigation() {
    const links = document.querySelectorAll("a[href]");
    links.forEach((link) => {
      link.addEventListener("click", function (e) {
        const href = this.getAttribute("href");

        // Skip external links and anchors
        if (
          href.startsWith("http") ||
          href.startsWith("#") ||
          href.startsWith("mailto:") ||
          href.startsWith("tel:")
        ) {
          return;
        }

        // Track internal navigation
        navigationState.isNavigating = true;

        // Add to history state
        if (window.history && window.history.pushState) {
          window.history.pushState(
            { url: href, timestamp: Date.now() },
            "",
            href
          );
        }

        // Reset navigation state after navigation
        setTimeout(() => {
          navigationState.isNavigating = false;
          navigationState.currentPage = href;
        }, 500);
      });
    });
  }

  // Prevent page reload on refresh
  function preventReloadOnRefresh() {
    // Store current state
    if (window.history && window.history.replaceState) {
      window.history.replaceState(
        {
          url: window.location.pathname,
          timestamp: Date.now(),
          isRefresh: true,
        },
        "",
        window.location.pathname
      );
    }

    // Handle page refresh
    window.addEventListener("beforeunload", function (e) {
      // Clear any cached data that might cause issues
      if (window.sessionStorage) {
        window.sessionStorage.removeItem("navigationState");
      }
    });
  }

  // Fix browser back button behavior
  function fixBackButton() {
    // Override the back button behavior
    document.addEventListener("keydown", function (e) {
      // Check for Alt+Left (back) or Backspace (in some browsers)
      if (
        (e.altKey && e.keyCode === 37) ||
        (e.keyCode === 8 &&
          e.target.tagName !== "INPUT" &&
          e.target.tagName !== "TEXTAREA")
      ) {
        e.preventDefault();

        // If user is authenticated, redirect to CV templates instead of previous page
        if (navigationState.isAuthenticated) {
          window.location.href = "/cv-templates/";
        } else {
          // Use proper navigation for non-authenticated users
          if (document.referrer && document.referrer !== window.location.href) {
            window.location.href = document.referrer;
          } else {
            window.location.href = "/";
          }
        }
      }
    });

    // Additional protection: Monitor URL changes
    let currentUrl = window.location.href;
    setInterval(function () {
      if (window.location.href !== currentUrl) {
        currentUrl = window.location.href;

        // If authenticated user navigated to auth page, redirect
        if (navigationState.isAuthenticated) {
          const authPages = [
            "/login/",
            "/register/",
            "/forgot-password/",
            "/reset-password/",
          ];
          if (
            authPages.some((page) => window.location.pathname.includes(page))
          ) {
            window.location.href = "/cv-templates/";
          }
        }
      }
    }, 100);
  }

  // Initialize all fixes when DOM is ready
  function initializeNavigationFixes() {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () {
        checkAuthenticationStatus();
        handleNavigation();
        fixFormNavigation();
        fixLinkNavigation();
        preventReloadOnRefresh();
        fixBackButton();
      });
    } else {
      checkAuthenticationStatus();
      handleNavigation();
      fixFormNavigation();
      fixLinkNavigation();
      preventReloadOnRefresh();
      fixBackButton();
    }
  }

  // Start the fixes
  initializeNavigationFixes();

  // Expose navigation state for debugging
  window.navigationState = navigationState;
})();
