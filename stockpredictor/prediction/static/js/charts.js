// Pie chart
const pieCtx = document.getElementById("stockPieChart");
new Chart(pieCtx, {
  type: "doughnut",
  data: {
    labels: ["Hyundai", "Alibaba", "Apple", "Google"],
    datasets: [
      {
        data: [2534.1, 2638.8, 6339.8, 4236.9],
        backgroundColor: ["#6A75CA", "#D93025", "#00B67A", "#F4B400"],
        borderWidth: 1,
      },
    ],
  },
  options: {
    cutout: "70%",
  },
});

// Bar chart
const trendCtx = document.getElementById("trendChart");
new Chart(trendCtx, {
  type: "bar",
  data: {
    labels: ["Jan", "Feb", "Mar", "Apr"],
    datasets: [
      {
        label: "Apple",
        data: [80000, 90000, 70000, 100000],
        backgroundColor: "#00B67A",
      },
      {
        label: "Alibaba",
        data: [60000, 50000, 75000, 65000],
        backgroundColor: "#D93025",
      },
      {
        label: "Google",
        data: [40000, 55000, 60000, 85000],
        backgroundColor: "#F4B400",
      },
    ],
  },
  options: {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },
});
