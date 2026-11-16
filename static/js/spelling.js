/* Spelling & grammar checker (free-text tool) + "listen and spell" word
   practice game. Both live on the /spelling page. */

(function () {
  document.addEventListener("DOMContentLoaded", function () {
    // ---------------- Free-text checker ----------------
    const checkBtn = document.getElementById("check-text-btn");
    const textArea = document.getElementById("check-text-input");
    const resultsBox = document.getElementById("check-results");

    if (checkBtn && textArea) {
      checkBtn.addEventListener("click", function () {
        const text = textArea.value.trim();
        if (!text) return;
        checkBtn.disabled = true;
        checkBtn.textContent = "Checking…";

        fetch("/spelling/check", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text, save_progress: true }),
        })
          .then(function (r) { return r.json(); })
          .then(renderCheckResults)
          .catch(function () {
            resultsBox.innerHTML = "<p>Something went wrong. Please try again.</p>";
          })
          .finally(function () {
            checkBtn.disabled = false;
            checkBtn.textContent = "Check my writing";
          });
      });
    }

    function renderCheckResults(data) {
      if (data.error) {
        resultsBox.innerHTML = "<p>" + data.error + "</p>";
        return;
      }
      let html = '<div class="flex items-center gap-12 mt-16">';
      html += '<span class="score-pill">' + Math.round(data.score) + "%</span>";
      html += "<p class='mb-0'>" + (data.spelling_issues.length + data.grammar_issues.length) +
        " thing(s) to look at.</p></div>";

      if (data.spelling_issues.length) {
        html += "<h4 class='mt-16'>Spelling</h4><ul>";
        data.spelling_issues.forEach(function (issue) {
          html += "<li><strong>" + issue.word + "</strong> → did you mean <strong>" +
            issue.suggestion + "</strong>?</li>";
        });
        html += "</ul>";
      }

      if (data.grammar_issues.length) {
        html += "<h4 class='mt-16'>Grammar</h4><ul>";
        data.grammar_issues.forEach(function (issue) {
          html += "<li>" + issue.message;
          if (issue.suggestion) html += " (try: <strong>" + issue.suggestion + "</strong>)";
          html += "</li>";
        });
        html += "</ul>";
      } else if (!data.online_available) {
        html +=
          "<p class='muted mt-16' style='font-size:0.85rem'>Grammar checking needs an internet " +
          "connection — only offline spelling was checked this time.</p>";
      }

      if (!data.spelling_issues.length && !data.grammar_issues.length) {
        html += "<p class='mt-16'>Looks great — no issues found! 🎉</p>";
      }

      resultsBox.innerHTML = html;
    }

    // ---------------- Listen & spell practice ----------------
    const practiceForm = document.getElementById("spelling-practice-form");
    if (practiceForm) {
      const submitBtn = document.getElementById("spelling-practice-submit");
      const resultBox = document.getElementById("spelling-practice-result");

      submitBtn.addEventListener("click", function () {
        const inputs = practiceForm.querySelectorAll("[data-target-word]");
        const words = [];
        inputs.forEach(function (input) {
          words.push({ target: input.getAttribute("data-target-word"), answer: input.value });
        });

        submitBtn.disabled = true;
        fetch("/spelling/practice/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ words: words }),
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            submitBtn.disabled = false;
            if (data.error) {
              resultBox.innerHTML = "<p>" + data.error + "</p>";
              return;
            }
            resultBox.innerHTML =
              '<div class="flex items-center gap-12">' +
              '<span class="score-pill">' + Math.round(data.score) + "%</span>" +
              "<p class='mb-0'>You got " + data.correct + " out of " + data.total + " correct!</p>" +
              "</div>";
          })
          .catch(function () {
            submitBtn.disabled = false;
            resultBox.innerHTML = "<p>Something went wrong. Please try again.</p>";
          });
      });
    }
  });
})();
