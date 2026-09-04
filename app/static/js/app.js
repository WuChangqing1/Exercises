(function () {
  var tokenEl = document.querySelector('meta[name="csrf-token"]');
  var token = tokenEl ? tokenEl.getAttribute("content") : "";

  if (token) {
    document.body.addEventListener("htmx:configRequest", function (e) {
      e.detail.headers["X-CSRF-Token"] = token;
    });
  }

  if ("serviceWorker" in navigator && window.location.pathname.indexOf("/training/") === 0) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/training/sw.js", { scope: "/training/" }).catch(function () {});
    });
  }
})();
