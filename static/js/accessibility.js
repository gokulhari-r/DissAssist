/* Accessibility settings flyout (bottom-right gear button on every page).
   Stores preferences in localStorage for instant effect, and — for logged
   in students — also saves them to the server via /profile so they persist
   across devices/browsers. */

(function () {
  function applyPrefs(prefs) {
    document.documentElement.style.setProperty("--user-font-size", prefs.fontSize + "px");
    document.documentElement.style.setProperty("--user-line-spacing", prefs.lineSpacing);
    document.body.classList.toggle("font-dyslexic", prefs.font === "opendyslexic");
  }

  function loadPrefs() {
    const stored = localStorage.getItem("ldhub-prefs");
    if (stored) {
      try { return JSON.parse(stored); } catch (e) { /* ignore */ }
    }
    if (window.SERVER_PREFS) return window.SERVER_PREFS;
    return { font: "atkinson", fontSize: 18, lineSpacing: 1.6 };
  }

  function savePrefs(prefs) {
    localStorage.setItem("ldhub-prefs", JSON.stringify(prefs));
  }

  document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("settings-toggle");
    const flyout = document.getElementById("settings-flyout");
    if (!toggleBtn || !flyout) return;

    const fontSelect = document.getElementById("pref-font");
    const sizeRange = document.getElementById("pref-size");
    const spacingRange = document.getElementById("pref-spacing");

    let prefs = loadPrefs();
    if (fontSelect) fontSelect.value = prefs.font;
    if (sizeRange) sizeRange.value = prefs.fontSize;
    if (spacingRange) spacingRange.value = prefs.lineSpacing;
    applyPrefs(prefs);

    toggleBtn.addEventListener("click", function () {
      flyout.classList.toggle("open");
    });

    function update() {
      prefs = {
        font: fontSelect ? fontSelect.value : prefs.font,
        fontSize: sizeRange ? parseInt(sizeRange.value, 10) : prefs.fontSize,
        lineSpacing: spacingRange ? parseFloat(spacingRange.value) : prefs.lineSpacing,
      };
      applyPrefs(prefs);
      savePrefs(prefs);
    }

    [fontSelect, sizeRange, spacingRange].forEach(function (el) {
      if (el) el.addEventListener("input", update);
    });

    const saveBtn = document.getElementById("pref-save-server");
    if (saveBtn) {
      saveBtn.addEventListener("click", function () {
        const form = new FormData();
        form.append("name", document.body.dataset.userName || "");
        form.append("preferred_font", prefs.font);
        form.append("font_size", prefs.fontSize);
        form.append("line_spacing", prefs.lineSpacing);
        fetch("/profile", { method: "POST", body: form }).then(function () {
          saveBtn.textContent = "Saved!";
          setTimeout(function () { saveBtn.textContent = "Save to my account"; }, 1500);
        });
      });
    }
  });
})();
