Chart.defaults.color = 'rgba(255, 255, 255, 0.7)';
Chart.defaults.font.family = "'DM Sans', sans-serif";
Chart.defaults.scale.grid.color = 'rgba(255, 255, 255, 0.05)';

let rainfallChartInstance = null;
let sensorChartInstance = null;

async function initRainfallChart(canvasId) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const data = await fetch('/api/weather/history?hours=24').then(r => r.json());
  const labels = data.map(d => new Date(d.timestamp).getHours() + ':00');
  const rainData = data.map(d => d.rainfall_mm);
  const riskData = data.map(d => d.risk_score);

  if (rainfallChartInstance) rainfallChartInstance.destroy();

  rainfallChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Rainfall (mm)',
          data: rainData,
          type: 'bar',
          backgroundColor: 'rgba(0, 212, 255, 0.3)',
          borderColor: '#00D4FF',
          borderWidth: 1,
          yAxisID: 'y'
        },
        {
          label: 'Risk Score (%)',
          data: riskData,
          type: 'line',
          borderColor: '#FF3B3B',
          backgroundColor: 'rgba(255, 59, 59, 0.1)',
          fill: true,
          tension: 0.4,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: { type: 'linear', display: true, position: 'left', title: {display: true, text: 'Rainfall & Level'} },
        y1: { type: 'linear', display: true, position: 'right', min: 0, max: 100, grid: {drawOnChartArea: false} }
      }
    }
  });

  // Auto update every 60s
  setInterval(async () => {
    const newData = await fetch('/api/weather/history?hours=24').then(r => r.json());
    rainfallChartInstance.data.labels = newData.map(d => new Date(d.timestamp).getHours() + ':00');
    rainfallChartInstance.data.datasets[0].data = newData.map(d => d.rainfall_mm);
    rainfallChartInstance.data.datasets[1].data = newData.map(d => d.risk_score);
    rainfallChartInstance.update('quiet');
  }, 60000);
}

function initRiskGauge(canvasId, score) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  
  const color = score > 66 ? '#FF3B3B' : score > 33 ? '#FF8C00' : '#00FF88';
  
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Risk', 'Safe'],
      datasets: [{
        data: [score, 100 - score],
        backgroundColor: [color, 'rgba(255, 255, 255, 0.1)'],
        borderWidth: 0,
        circumference: 270,
        rotation: 225,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '80%',
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false }
      }
    },
    plugins: [{
      id: 'textCenter',
      beforeDraw: function(chart) {
        var width = chart.width, height = chart.height, ctx = chart.ctx;
        ctx.restore();
        var fontSize = (height / 80).toFixed(2);
        ctx.font = "bold " + fontSize + "em Rajdhani";
        ctx.textBaseline = "middle";
        ctx.fillStyle = "#fff";
        var text = Math.round(score) + "%",
            textX = Math.round((width - ctx.measureText(text).width) / 2),
            textY = height / 1.8;
        ctx.fillText(text, textX, textY);
        ctx.save();
      }
    }]
  });
}

async function initSensorChart(canvasId) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const sensors = await fetch('/api/sensors').then(r => r.json());
  
  // Create mock historical data for purely demo purposes for lines
  const labels = Array.from({length: 12}, (_, i) => `-${12-i}m`);
  labels.push('Now');
  
  const colors = ['#00D4FF', '#00FF88', '#FF8C00', '#FF3B3B', '#B400FF'];
  
  const datasets = sensors.map((s, i) => {
    const base = s.water_level_cm;
    const data = Array.from({length: 12}, () => Math.max(0, base + (Math.random() * 20 - 10)));
    data.push(base);
    return {
      label: s.name,
      data: data,
      borderColor: colors[i % colors.length],
      tension: 0.4,
      borderWidth: 2,
      pointRadius: 0
    };
  });

  if (sensorChartInstance) sensorChartInstance.destroy();

  sensorChartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'nearest', axis: 'x', intersect: false },
      plugins: { legend: { position: 'right', labels: {boxWidth: 10} } },
      scales: { y: { title: {display: true, text: 'Level (cm)'} } }
    }
  });

  setInterval(async () => {
    const newSensors = await fetch('/api/sensors').then(r => r.json());
    newSensors.forEach((ns, i) => {
      datasets[i].data.shift();
      datasets[i].data.push(ns.water_level_cm);
    });
    sensorChartInstance.update('quiet');
  }, 30000);
}
