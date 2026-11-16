/* Speech-to-text practice page logic, built on the browser's
   SpeechRecognition API (webkitSpeechRecognition in Chrome/Edge).
   Lets the student record themselves reading the target sentence,
   shows a live transcript, then scores it against the target text. */

(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const micBtn = document.getElementById("mic-btn");
    if (!micBtn) return; // not on the speech practice page

    const transcriptBox = document.getElementById("transcript-box");
    const statusEl = document.getElementById("speech-status");
    const submitBtn = document.getElementById("speech-submit-btn");
    const resultBox = document.getElementById("speech-result");
    const targetSentence = micBtn.getAttribute("data-target-sentence");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      statusEl.textContent =
        "Speech recognition isn't supported in this browser. Try Chrome or Edge on desktop or Android.";
      micBtn.disabled = true;
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = true;

    let recording = false;
    let finalTranscript = "";

    micBtn.addEventListener("click", function () {
      if (recording) {
        recognition.stop();
        return;
      }
      finalTranscript = "";
      transcriptBox.textContent = "Listening…";
      micBtn.classList.add("recording");
      micBtn.textContent = "⏹";
      statusEl.textContent = "Recording — speak the sentence above.";
      recording = true;
      recognition.start();
    });

    recognition.onresult = function (event) {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptPiece = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcriptPiece + " ";
        } else {
          interim += transcriptPiece;
        }
      }
      transcriptBox.textContent = (finalTranscript + interim).trim() || "Listening…";
    };

    recognition.onerror = function (event) {
      statusEl.textContent = "Microphone error: " + event.error + ". Please check microphone permissions.";
    };

    recognition.onend = function () {
      recording = false;
      micBtn.classList.remove("recording");
      micBtn.textContent = "🎤";
      statusEl.textContent = "Done recording. Review the text below, then submit.";
      if (finalTranscript.trim()) {
        submitBtn.disabled = false;
      }
    };

    submitBtn.addEventListener("click", function () {
      const transcript = transcriptBox.textContent.trim();
      submitBtn.disabled = true;
      submitBtn.textContent = "Checking…";

      fetch("/speech/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: transcript, target_sentence: targetSentence }),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          submitBtn.textContent = "Check my reading";
          if (data.error) {
            resultBox.innerHTML = "<p>" + data.error + "</p>";
            return;
          }
          resultBox.innerHTML =
            '<div class="flex items-center gap-12">' +
            '<span class="score-pill">' + Math.round(data.score) + "%</span>" +
            "<p class='mb-0'>" + data.feedback + "</p>" +
            "</div>";
        })
        .catch(function () {
          submitBtn.disabled = false;
          submitBtn.textContent = "Check my reading";
          resultBox.innerHTML = "<p>Something went wrong. Please try again.</p>";
        });
    });
  });
})();
