var App = {
  //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main

  system: "",
  translations: {},
  contents: {},

  escapeHtml: function (text) {
    var map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return text.replace(/[&<>"']/g, function (m) {
      return map[m];
    });
  },

  translation: function (classname) {
    var wrapper = document.querySelector("translation");
    if (!wrapper) return;

    wrapper.innerHTML += '<img src="" alt=" " />';
    switchLanguage(wrapper);

    function switchLanguage(wrapper) {
      var flag = wrapper.querySelector("img");
      var languages = wrapper
        .getAttribute("languages")
        .split(",")
        .map((lang) => lang.trim());

      var current = App.language();
      let currentIndex = languages.indexOf(current);
      if (currentIndex === -1) currentIndex = 0;

      var next = languages[(currentIndex + 1) % languages.length];

      flag.src = `/assets/${next}.png`;
      flag.onclick = () => {
        App.translate(next);
        switchLanguage(wrapper);
      };
    }
  },

  /** (AI-USE) - Get current language name e.g "en";
   * App.language();
   */
  language: function () {
    if (!$.cookie("translate")) return "en";
    return $.cookie("translate");
  },

  /** (AI-USE) - Set project language translation;
   * App.translate("en");
   */
  translate: function (lng = "") {
    if (!lng) return false;
    if (!this.translations[lng] && lng != "en") {
      App.failed("Could not set language");
      $.cookie("translate", "en", { secure: location.protocol === "https:", sameSite: "Lax" });
      return false;
    }

    $.cookie("translate", lng, { secure: location.protocol === "https:", sameSite: "Lax" });
    document.querySelectorAll("[translate]").forEach((el) => {
      var key = el.getAttribute("translate");
      el.innerHTML = App.lng(key, el.innerHTML);
    });

    return true;
  },

  /** (AI-USE) - Display failure message;
   * App.failed("Failed to load request.");
   */
  failed: function (message = "") {
    App._showToast(message, "error");
  },

  /** (AI-USE) - Display info message;
   * App.info("Account created.");
   */
  info: function (message = "") {
    App._showToast(message, "info");
  },

  /** (AI-USE) - Display successful message;
   * App.done("Loaded items.");
   */
  done: function (message = "") {
    App._showToast(message, "success");
  },

  // [SECURITY]
  /** (AI-USE) - Call PHP backend methods via AJAX;
   * // Params:
   * // page - PHP class file name (without .php)
   * // method - Public method name in PHP class
   * // data - Data to send (e.g {name: '...', image: '...base64...'})
   * // code - Callback function to handle json response
   * App.call("dashboard", "signOut", {}, (echo) => {
   *   if(echo && echo.error){
   *     App.failed(echo.message || "Failed to sign out.");
   *     return;
   *   }
   *   window.location.href = "/signin";
   * });
   */
  call: function (page = "", method = "", data = {}, code, options = {}) {
    setTimeout(() => {
      var maxRetries = Number(options.maxRetries || 2);
      var attempt = 0;

      var getBackoffDelay = function (retry) {
        var base = 500;
        var delay = Math.min(5000, base * Math.pow(2, retry));
        return delay + Math.floor(Math.random() * 300);
      };

      var sendRequest = function () {
        var result = null;

        $.ajax({
          url: page.toLowerCase(),
          type: "POST",
          async: false,
          data: { "system-call": method, ...data },
          headers: { "X-System": App.system },
          xhrFields: { withCredentials: true },
          timeout: 12000,
          success: function (response) {
            if (response.hasOwnProperty("system")) {
              App.system = response.system;
              delete response.system;
            }
            result = response;
          },
          error: function (xhr, status, err) {
            if (xhr.status === 429 && attempt < maxRetries) {
              attempt += 1;
              var until = Date.now() + getBackoffDelay(attempt);
              while (Date.now() < until) {}
              sendRequest();
              return;
            }
            if (xhr.status === 401) {
              App.failed("Unauthorized.");
            } else if (xhr.status === 403) {
              App.failed("Forbidden / CSRF failed.");
            } else if (xhr.status === 429) {
              App.failed("Too many requests. Please wait before retrying.");
            } else {
              App.failed("Call failed: " + err);
            }
          },
        });

        if (result !== null && typeof code === "function") {
          code(result);
        }
      };

      sendRequest();
    }, 0);
  },

  lng: function (key = "", text = "") {
    if (!key || !text) return text;

    var lng = this.language();
    if (this.translations[lng] && this.translations[lng][key]) {
      if (!App.contents[key]) App.contents[key] = text;
      return this.translations[lng][key];
    } else if (App.contents[key]) {
      return App.contents[key];
    }

    return text;
  },

  //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Internal

  loaded: function loaded() {
    App.translate(App.language());
    App.translation();

    setTimeout(() => {
      $("#system-loader").fadeOut("slow");
    }, 500);
    setTimeout(() => {
      $("#system-loader").remove();
    }, 1500);
  },

  //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers

  _initToastContainer: function () {
    if ($("#system-toast-container").length === 0) {
      $("body").append('<div id="system-toast-container"></div>');
    }
  },

  _showToast: function (message, type) {
    this._initToastContainer();

    var colors = {
      error: "rgb(252, 70, 70)",
      info: "rgb(51, 179, 218)",
      success: "rgb(51, 218, 58)",
    };
    var icons = {
      error: "fa-circle-xmark",
      info: "fa-circle-question",
      success: "fa-circle-check",
    };

    var borderColor = colors[type] || "#333";
    var iconClass = icons[type] || "fa-circle-info";

    var toast = $("<div></div>")
      .addClass("system-toast")
      .addClass("system-toast-" + type)
      .append($("<i></i>").addClass(`fa-regular ${iconClass}`).css({ "font-size": "24px", "font-weight": "normal", color: borderColor }), $("<span></span>").text(message).css({ color: borderColor }))
      .appendTo("#system-toast-container")
      .animate({ opacity: 1, right: "0px" }, 300);

    setTimeout(() => {
      toast.animate({ opacity: 0, right: "-20px" }, 300, function () {
        $(this).remove();
      });
    }, 3000);

    toast.on("click", function () {
      $(this).remove();
    });
  },
};
