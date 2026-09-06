(function () {
  var data = window.__CHARTS__ || {};
  if (!data.labels || !data.labels.length || typeof Chart === "undefined") return;

  var base = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
  };

  var exists = function (id) {
    return document.getElementById(id) !== null;
  };

  if (exists("chart-exercised")) {
    new Chart(document.getElementById("chart-exercised"), {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [{ label: "运动天数", data: data.exercised, backgroundColor: "#10b981" }],
      },
      options: Object.assign({}, base, { scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }),
    });
  }

  if (exists("chart-pullup")) {
    new Chart(document.getElementById("chart-pullup"), {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [{ label: "单组最高", data: data.pullup_max, borderColor: "#6366f1", fill: false, tension: 0.3 }],
      },
      options: base,
    });
  }

  if (exists("chart-run")) {
    new Chart(document.getElementById("chart-run"), {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [{ label: "跑量 km", data: data.run_km, backgroundColor: "#f59e0b" }],
      },
      options: base,
    });
  }
})();
