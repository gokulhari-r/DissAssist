/* Renders the "progress over time" line chart on student & guardian
   dashboards. Expects a <canvas id="progress-chart" data-student-id="..">
   element on the page, and assumes Chart.js has been loaded from CDN. */

(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("progress-chart");
    if (!canvas || typeof Chart === "undefined") return;

    const studentId = canvas.getAttribute("data-student-id");

    fetch("/api/progress/" + studentId)
      .then(function (r) { return r.json(); })
      .then(function (rows) {
        if (!rows.length) {
          canvas.replaceWith(
            Object.assign(document.createElement("p"), {
              className: "muted",
              textContent: "No activities completed yet — once they try an activity, progress will show up here.",
            })
          );
          return;
        }

        const labels = rows.map(function (r) { return r.date; });
        const byType = {};
        rows.forEach(function (r) {
          if (!byType[r.activity_type]) byType[r.activity_type] = [];
          byType[r.activity_type].push(r.score);
        });

        const colors = {
          reading: "#3D8B83",
          spelling: "#7B6FB0",
          handwriting: "#E8794A",
          speech: "#C97A1F",
        };

        const datasets = Object.keys(byType).map(function (type) {
          return {
            label: type.charAt(0).toUpperCase() + type.slice(1),
            data: byType[type],
            borderColor: colors[type] || "#3D8B83",
            backgroundColor: colors[type] || "#3D8B83",
            tension: 0.3,
            fill: false,
          };
        });

        new Chart(canvas, {
          type: "line",
          data: { labels: labels, datasets: datasets },
          options: {
            responsive: true,
            scales: { y: { min: 0, max: 100, ticks: { stepSize: 20 } } },
            plugins: { legend: { position: "bottom" } },
          },
        });
      })
      .catch(function () {
        /* fail silently — chart is a nice-to-have, not critical */
      });
  });
})();
