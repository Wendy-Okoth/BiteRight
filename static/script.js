// static/script.js
document.addEventListener("DOMContentLoaded", () => {
  // Parse server JSON blob safely
  const dataEl = document.getElementById("biteright-data");
  let appData = {
    total_calories: 0,
    total_protein: 0,
    total_fat: 0,
    daily_labels: [],
    daily_calories: []
  };

  if (dataEl) {
    try {
      // Use textContent to avoid HTML escaping issues
      appData = JSON.parse(dataEl.textContent || dataEl.innerText);
    } catch (err) {
      console.error("BiteRight: failed to parse embedded JSON data:", err);
    }
  } else {
    console.warn("BiteRight: no embedded data element found (biteright-data)");
  }

  // Normalise values
  const totalCalories = Number(appData.total_calories) || 0;
  const totalProtein = Number(appData.total_protein) || 0;
  const totalFat = Number(appData.total_fat) || 0;
  const dailyLabels = Array.isArray(appData.daily_labels) ? appData.daily_labels : [];
  const dailyCalories = Array.isArray(appData.daily_calories) ? appData.daily_calories.map(n => Number(n) || 0) : [];

  // PIE: Nutrition Breakdown
  try {
    const ctxPie = document.getElementById("nutritionChart");
    if (ctxPie) {
      new Chart(ctxPie, {
        type: "pie",
        data: {
          labels: ["Calories", "Protein (g)", "Fat (g)"],
          datasets: [{
            data: [totalCalories, totalProtein, totalFat],
            backgroundColor: ["#ef4444", "#ec4899", "#8b5cf6"]
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { position: "bottom" } }
        }
      });
    }
  } catch (e) {
    console.error("BiteRight: error creating pie chart:", e);
  }

  // BAR: Calories per Day (only if we have labels)
  try {
    const ctxBar = document.getElementById("calorieTrendChart");
    if (ctxBar && dailyLabels.length > 0) {
      new Chart(ctxBar, {
        type: "bar",
        data: {
          labels: dailyLabels,
          datasets: [{
            label: "Calories",
            data: dailyCalories,
            backgroundColor: "#ef4444"
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true, title: { display: true, text: "Calories" } },
            x: { title: { display: true, text: "Date" } }
          }
        }
      });
    } else {
      // optional: clear canvas or show message
      if (ctxBar) {
        const ctx = ctxBar.getContext("2d");
        ctx.clearRect(0,0,ctxBar.width,ctxBar.height);
      }
    }
  } catch (e) {
    console.error("BiteRight: error creating bar chart:", e);
  }
});

