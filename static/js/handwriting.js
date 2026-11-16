/* Handwriting practice canvas: lets the student draw with mouse, pen, or
   touch, then exports the drawing as a PNG and sends it to the server
   for analysis (see utils/handwriting_check.py). */

(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("handwriting-canvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    ctx.lineWidth = 6;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#2C2A26";

    let drawing = false;
    let lastX = 0;
    let lastY = 0;

    function getPos(evt) {
      const rect = canvas.getBoundingClientRect();
      const clientX = evt.touches ? evt.touches[0].clientX : evt.clientX;
      const clientY = evt.touches ? evt.touches[0].clientY : evt.clientY;
      return {
        x: ((clientX - rect.left) / rect.width) * canvas.width,
        y: ((clientY - rect.top) / rect.height) * canvas.height,
      };
    }

    function start(evt) {
      evt.preventDefault();
      drawing = true;
      const pos = getPos(evt);
      lastX = pos.x;
      lastY = pos.y;
    }

    function move(evt) {
      if (!drawing) return;
      evt.preventDefault();
      const pos = getPos(evt);
      ctx.beginPath();
      ctx.moveTo(lastX, lastY);
      ctx.lineTo(pos.x, pos.y);
      ctx.stroke();
      lastX = pos.x;
      lastY = pos.y;
    }

    function end() {
      drawing = false;
    }

    canvas.addEventListener("mousedown", start);
    canvas.addEventListener("mousemove", move);
    canvas.addEventListener("mouseup", end);
    canvas.addEventListener("mouseleave", end);
    canvas.addEventListener("touchstart", start, { passive: false });
    canvas.addEventListener("touchmove", move, { passive: false });
    canvas.addEventListener("touchend", end);

    function clearCanvas() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    clearCanvas();

    const clearBtn = document.getElementById("clear-canvas-btn");
    if (clearBtn) clearBtn.addEventListener("click", clearCanvas);

    const submitBtn = document.getElementById("submit-handwriting-btn");
    const feedbackBox = document.getElementById("handwriting-feedback");
    const targetWord = canvas.getAttribute("data-target-word");

    if (submitBtn) {
      submitBtn.addEventListener("click", function () {
        const dataUrl = canvas.toDataURL("image/png");
        submitBtn.disabled = true;
        submitBtn.textContent = "Checking…";

        fetch("/handwriting/check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: dataUrl, target_word: targetWord }),
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            submitBtn.disabled = false;
            submitBtn.textContent = "Check my writing";
            if (data.error) {
              feedbackBox.innerHTML = "<p>" + data.error + "</p>";
              return;
            }
            let ocrLine = "";
            if (data.ocr) {
              ocrLine = data.ocr.matched
                ? "<p>✅ Letter/word recognition matched your target!</p>"
                : "<p>I read this as: “" + data.ocr.recognised_text + "”</p>";
            } else if (!data.ocr_available) {
              ocrLine =
                "<p class='muted' style='font-size:0.85rem'>(Tip: install Tesseract OCR for automatic " +
                "letter recognition feedback — shape feedback below always works.)</p>";
            }
            feedbackBox.innerHTML =
              '<div class="flex items-center gap-12">' +
              '<span class="score-pill">' + Math.round(data.score) + "%</span>" +
              "<p class='mb-0'>" + data.feedback + "</p>" +
              "</div>" + ocrLine;
          })
          .catch(function () {
            submitBtn.disabled = false;
            submitBtn.textContent = "Check my writing";
            feedbackBox.innerHTML = "<p>Something went wrong. Please try again.</p>";
          });
      });
    }
  });
})();
