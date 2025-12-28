(function () {
  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  // Password strength checker
  function checkPasswordStrength(password) {
    let strength = 0;
    let strengthText = "";
    let strengthClass = "";

    if (password.length >= 8) strength += 1;
    if (password.match(/[a-z]/)) strength += 1;
    if (password.match(/[A-Z]/)) strength += 1;
    if (password.match(/[0-9]/)) strength += 1;
    if (password.match(/[^a-zA-Z0-9]/)) strength += 1;

    if (strength < 2) {
      strengthText = "Weak";
      strengthClass = "weak";
    } else if (strength < 3) {
      strengthText = "Fair";
      strengthClass = "fair";
    } else if (strength < 4) {
      strengthText = "Good";
      strengthClass = "good";
    } else {
      strengthText = "Strong";
      strengthClass = "strong";
    }

    return { strength, strengthText, strengthClass };
  }

  // Form persistence functions
  function saveFormData(form) {
    const formData = new FormData(form);
    const data = {};
    for (let [key, value] of formData.entries()) {
      if (key !== "csrfmiddlewaretoken") {
        data[key] = value;
      }
    }
    localStorage.setItem("authFormData", JSON.stringify(data));
  }

  function loadFormData(form) {
    const savedData = localStorage.getItem("authFormData");
    if (savedData) {
      try {
        const data = JSON.parse(savedData);
        Object.keys(data).forEach((key) => {
          const input = form.querySelector(`[name="${key}"]`);
          if (input && input.type !== "password") {
            input.value = data[key];
          }
        });
      } catch (e) {
        console.log("Error loading form data:", e);
      }
    }
  }

  function clearFormData() {
    localStorage.removeItem("authFormData");
  }

  onReady(function () {
    // Password toggles
    var passwordToggles = document.querySelectorAll(".password-toggle");
    passwordToggles.forEach(function (toggle) {
      toggle.addEventListener("click", function (e) {
        e.preventDefault();
        var input = this.parentElement.querySelector("input");
        var showing = input.getAttribute("type") === "text";
        input.setAttribute("type", showing ? "password" : "text");
        var icon = this.querySelector("i");
        if (icon) icon.className = showing ? "fas fa-eye" : "fas fa-eye-slash";
      });
    });

    // Password strength indicator
    var passwordInput = document.getElementById("password");
    if (passwordInput) {
      var strengthFill = document.getElementById("strengthFill");
      var strengthText = document.getElementById("strengthText");

      passwordInput.addEventListener("input", function () {
        var password = this.value;
        if (password.length === 0) {
          if (strengthFill) {
            strengthFill.className = "strength-fill";
            strengthFill.style.width = "0%";
          }
          if (strengthText) {
            strengthText.textContent = "Enter password";
            strengthText.className = "strength-text";
          }
        } else {
          var result = checkPasswordStrength(password);
          if (strengthFill) {
            strengthFill.className = "strength-fill " + result.strengthClass;
          }
          if (strengthText) {
            strengthText.textContent = result.strengthText;
            strengthText.className = "strength-text " + result.strengthClass;
          }
        }
      });
    }

    // Form persistence
    var forms = document.querySelectorAll(".auth-form");
    forms.forEach(function (form) {
      // Load saved data on page load
      loadFormData(form);

      // Save data on input change
      var inputs = form.querySelectorAll(
        'input[type="text"], input[type="email"]'
      );
      inputs.forEach(function (input) {
        input.addEventListener("input", function () {
          saveFormData(form);
        });
      });

      // Clear data on successful submit
      form.addEventListener("submit", function () {
        setTimeout(function () {
          clearFormData();
        }, 1000);
      });
    });

    // Basic submit button loading state
    var authBtn = document.querySelector(".auth-btn");
    if (authBtn) {
      var form = authBtn.closest("form");
      if (form) {
        form.addEventListener("submit", function () {
          authBtn.classList.add("loading");
        });
      }
    }
  });
})();
