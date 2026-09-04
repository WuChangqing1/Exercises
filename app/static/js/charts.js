(function () {
  var data = window.__CHARTS__ || {};
  if (!data.labels || !data.labels.length || typeof Chart === "undefined") return;

  var base = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
  };

  new Chart(document.getElementById("chart-completion"), {
    type: "bar",
    data: {
      labels: data.labels,
      datasets: [{ label: "完成率", data: data.completion, backgroundColor: "#6366f1" }],
    },
    options: Object.assign({}, base, { scales: { y: { max: 100, beginAtZero: true } } }),
  });

  new Chart(document.getElementById("chart-pullup"), {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [{ label: "单组最高", data: data.pullup_max, borderColor: "#10b981", fill: false, tension: 0.3 }],
    },
    options: base,
  });

  new Chart(document.getElementById("chart-run"), {
    type: "bar",
    data: {
      labels: data.labels,
      datasets: [{ label: "跑量 km", data: data.run_km, backgroundColor: "#f59e0b" }],
    },
    options: base,
  });
})();
