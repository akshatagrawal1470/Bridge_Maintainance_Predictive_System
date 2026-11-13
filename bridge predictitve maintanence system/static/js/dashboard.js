const chartDefaults = {
  responsive: true,
  animation: false,
  maintainAspectRatio: true,
  plugins: { legend: { labels: { boxWidth: 10, usePointStyle: true } } },
  scales: {
    x: { ticks: { maxTicksLimit: 8 }, grid: { display: false } },
    y: { grid: { color: '#edf1f6' } }
  }
};

const vibrationChart = new Chart(document.getElementById('vibrationChart'), {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      { label: 'Ax', data: [], borderColor: '#2f80ed', backgroundColor: '#2f80ed', tension: 0.25, pointRadius: 0, borderWidth: 2 },
      { label: 'Ay', data: [], borderColor: '#0f766e', backgroundColor: '#0f766e', tension: 0.25, pointRadius: 0, borderWidth: 2 },
      { label: 'Az', data: [], borderColor: '#c88719', backgroundColor: '#c88719', tension: 0.25, pointRadius: 0, borderWidth: 2 }
    ]
  },
  options: chartDefaults
});

const fftChart = new Chart(document.getElementById('fftChart'), {
  type: 'bar',
  data: { labels: [], datasets: [{ label: 'Magnitude', data: [], backgroundColor: '#0f766e', borderRadius: 3 }] },
  options: chartDefaults
});

const featureLabels = {
  rms: 'RMS vibration',
  std_dev: 'Stability variation',
  energy: 'Vibration energy',
  peak_frequency: 'Peak frequency',
  peak_magnitude: 'Peak magnitude',
  spectral_centroid: 'Spectral centroid'
};

function statusClass(status) {
  return String(status).toLowerCase();
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function updateDashboard(payload) {
  const { latest, series, fft, features, prediction, crack, summary, history } = payload;
  setText('axValue', latest.ax.toFixed(3));
  setText('ayValue', latest.ay.toFixed(3));
  setText('azValue', latest.az.toFixed(3));
  setText('tempValue', latest.temperature.toFixed(1));
  setText('confidenceValue', prediction.confidence);
  setText('healthScore', `${prediction.health}%`);
  setText('statusText', prediction.status);
  setText('sourceText', prediction.source);
  setText('crackSeverity', crack.severity.toFixed(1));
  setText('crackStatus', crack.status);
  setText('crackStatusMetric', crack.status);
  setText('crackProbability', `${crack.probability.toFixed(1)}%`);
  setText('conditionText', summary.condition);

  const priorityBadge = document.getElementById('priorityBadge');
  priorityBadge.textContent = `${summary.priority} maintenance`;
  priorityBadge.className = `priority-badge ${String(summary.priority).toLowerCase()}`;

  document.getElementById('recommendationsList').innerHTML = summary.recommendations
    .slice(0, 4)
    .map(item => `<span>${item}</span>`)
    .join('');

  const ring = document.querySelector('.health-ring');
  const color = prediction.status === 'SAFE' ? '#11956f' : prediction.status === 'WARNING' ? '#c88719' : '#c94b45';
  ring.style.background = `conic-gradient(${color} 0deg, ${color} ${prediction.health * 3.6}deg, #d8e2ea ${prediction.health * 3.6}deg)`;

  vibrationChart.data.labels = series.labels;
  vibrationChart.data.datasets[0].data = series.ax;
  vibrationChart.data.datasets[1].data = series.ay;
  vibrationChart.data.datasets[2].data = series.az;
  vibrationChart.update();

  fftChart.data.labels = fft.frequency;
  fftChart.data.datasets[0].data = fft.magnitude;
  fftChart.update();

  document.getElementById('featureList').innerHTML = Object.entries(features)
    .map(([key, value]) => `<div><dt>${featureLabels[key] || key.replaceAll('_', ' ')}</dt><dd>${value}</dd></div>`)
    .join('');

  document.getElementById('historyTable').innerHTML = history
    .map(row => `
      <tr>
        <td>${row.time || String(row.timestamp).slice(11, 19)}</td>
        <td><span class="badge-status ${statusClass(row.status)}">${row.status}</span></td>
        <td>${row.health}%</td>
        <td>${row.crack_status}</td>
      </tr>
    `)
    .join('');
}

async function poll() {
  const response = await fetch('/api/live');
  updateDashboard(await response.json());
}

document.getElementById('crackForm').addEventListener('submit', async event => {
  event.preventDefault();
  const button = event.target.querySelector('button');
  button.disabled = true;
  button.textContent = 'Analyzing...';
  const response = await fetch('/api/crack-detect', {
    method: 'POST',
    body: new FormData(event.target)
  });
  const result = await response.json();
  button.disabled = false;
  button.textContent = 'Analyze Image';
  if (response.ok) {
    setText('crackStatus', result.status);
    setText('crackStatusMetric', result.status);
    setText('crackProbability', `${result.probability.toFixed(1)}%`);
    setText('crackSeverity', result.severity.toFixed(1));
    poll();
  } else {
    alert(result.error || 'Image analysis failed');
  }
});

poll();
setInterval(poll, 2500);
