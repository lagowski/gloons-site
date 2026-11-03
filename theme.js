// Theme toggle: System -> (opposite of the OS) -> (same as the OS) -> System,
// so the first click always visibly changes the page. Saved in localStorage("theme").
// The inline script in <head> applies the saved choice before first paint;
// "System" leaves data-theme unset so the prefers-color-scheme block decides.
(function () {
  var KEY = "theme";
  var root = document.documentElement;
  var osDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)");
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");

  function saved() {
    try {
      var t = localStorage.getItem(KEY);
      return t === "light" || t === "dark" ? t : "system";
    } catch (e) {
      return "system";
    }
  }

  function apply(pref) {
    if (pref === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", pref);
    var buttons = document.querySelectorAll(".theme-toggle");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute("aria-label", "Theme: " + pref);
      buttons[i].title = "Theme: " + pref + " (click to change)";
    }
  }

  function animate() {
    if (reduceMotion && reduceMotion.matches) return;
    var wipe = document.createElement("div");
    wipe.className = "theme-wipe";
    wipe.setAttribute("aria-hidden", "true");
    document.body.appendChild(wipe);
    root.classList.add("theme-switching");
    setTimeout(function () {
      root.classList.remove("theme-switching");
      wipe.remove();
    }, 300);
  }

  function next() {
    var order = osDark && osDark.matches ? ["light", "dark", "system"] : ["dark", "light", "system"];
    var pref = (current = order[(order.indexOf(current) + 1) % order.length]);
    try {
      localStorage.setItem(KEY, pref);
    } catch (e) {}
    animate();
    apply(pref);
  }

  var current = saved();
  apply(current);
  var buttons = document.querySelectorAll(".theme-toggle");
  for (var i = 0; i < buttons.length; i++) buttons[i].addEventListener("click", next);
})();
