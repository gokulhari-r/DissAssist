/* Text-to-speech helper built on the browser's built-in Web Speech API
   (SpeechSynthesis). No server or API key needed — works fully offline
   once the page is loaded, in any modern browser. */

(function () {
  const synth = window.speechSynthesis;
  let currentUtterance = null;

  function supported() {
    return "speechSynthesis" in window;
  }

  function speak(text, options) {
    options = options || {};
    const rate = options.rate || 0.9;
    const onWordBoundary = options.onWordBoundary;
    const onEnd = options.onEnd;

    if (!supported()) {
      alert("Sorry, text-to-speech isn't supported in this browser.");
      return;
    }
    stop();
    currentUtterance = new SpeechSynthesisUtterance(text);
    currentUtterance.rate = rate;
    currentUtterance.pitch = 1;

    if (onWordBoundary) {
      currentUtterance.onboundary = function (event) {
        if (event.name === "word") onWordBoundary(event.charIndex);
      };
    }
    if (onEnd) currentUtterance.onend = onEnd;

    synth.speak(currentUtterance);
  }

  function stop() {
    if (synth.speaking) synth.cancel();
  }

  window.LDHubTTS = { speak: speak, stop: stop, supported: supported };

  document.addEventListener("DOMContentLoaded", function () {
    // Generic "Listen" buttons: <button data-tts-target="#someElementId">
    document.querySelectorAll("[data-tts-target]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const target = document.querySelector(btn.getAttribute("data-tts-target"));
        if (!target) return;
        const rate = parseFloat(btn.getAttribute("data-tts-rate") || "0.9");
        btn.disabled = true;
        const originalLabel = btn.textContent;
        btn.textContent = "🔊 Reading aloud…";
        speak(target.innerText || target.textContent, {
          rate: rate,
          onEnd: function () {
            btn.disabled = false;
            btn.textContent = originalLabel;
          },
        });
      });
    });

    // Generic "Stop" buttons
    document.querySelectorAll("[data-tts-stop]").forEach(function (btn) {
      btn.addEventListener("click", stop);
    });

    // "Listen to this word" buttons used in spelling practice:
    // <button data-tts-word="apple">
    document.querySelectorAll("[data-tts-word]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        speak(btn.getAttribute("data-tts-word"), { rate: 0.8 });
      });
    });
  });
})();
