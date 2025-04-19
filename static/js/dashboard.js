document.addEventListener('DOMContentLoaded', function () {
  // Inicjalizacja stanu użytkownika
  const userData = JSON.parse(localStorage.getItem('user')) || { username: 'Użytkownik' };
  document.getElementById('username').textContent = userData.username;
  document.getElementById('userInitials').textContent = userData.username.charAt(0).toUpperCase();

  // Logika panelu bocznego
  const sidebar = document.getElementById('sidebar');
  document.getElementById('openSidebar').addEventListener('click', () => sidebar.classList.add('open'));
  document.getElementById('closeSidebar').addEventListener('click', () => sidebar.classList.remove('open'));

  // Obsługa wylogowania
  document.getElementById('logoutBtn').addEventListener('click', async function (e) {
    e.preventDefault();
    try {
      await fetch('/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
  });

  // Główna funkcja ładowania danych
  async function loadDashboardData() {
    const dateRange = document.getElementById('dateRange').value;
    const token = localStorage.getItem('access_token');

    if (!token) {
      window.location.href = '/login';
      return;
    }

    try {
      Swal.fire({
        title: 'Ładowanie danych',
        text: 'Proszę czekać...',
        allowOutsideClick: false,
        didOpen: () => Swal.showLoading()
      });

      const response = await fetch(`/api/health/dashboard?days=${dateRange}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch data');

      const data = await response.json();
      updateDashboard(data);
      Swal.close();
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      Swal.fire({
        title: 'Błąd',
        text: 'Nie udało się załadować danych. Spróbuj ponownie później.',
        icon: 'error',
        confirmButtonColor: '#10B981'
      });
    }
  }

  // Rejestracja event listenerów
  document.getElementById('refreshData').addEventListener('click', loadDashboardData);
  document.getElementById('dateRange').addEventListener('change', loadDashboardData);

  // Inicjalne ładowanie danych
  loadDashboardData();
});

// ========================
// FUNKCJE POMOCNICZE
// ========================

function updateDashboard(data) {
  const sampleData = {
    daily_stats: {
      steps: 7560,
      goal_steps: 10000,
      avg_heart_rate: 68,
      resting_heart_rate: 62,
      max_heart_rate: 142,
      sleep_hours: 7.5,
      goal_sleep_hours: 8,
      weight: 72.5,
      bmi: 22.1,
      weight_change: -0.5
    },
    charts: {
      activity: {
        labels: ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Nd'],
        steps: [8200, 7500, 9100, 10200, 7300, 8600, 7560],
        distance: [5.74, 5.25, 6.37, 7.14, 5.11, 6.02, 5.29]
      },
      heart_rate: {
        labels: ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Nd'],
        avg: [65, 67, 69, 71, 66, 64, 68],
        max: [120, 135, 142, 130, 128, 115, 142]
      },
      sleep: {
        labels: ['Pon', 'Wt', 'Śr', 'Czw', 'Pt', 'Sob', 'Nd'],
        hours: [7.2, 6.8, 8.1, 7.5, 6.9, 8.5, 7.5],
        quality: [80, 75, 90, 85, 70, 95, 85]
      },
      weight: {
        labels: ['1 Kwi', '8 Kwi', '15 Kwi', '22 Kwi', '29 Kwi', '6 Maj', '13 Maj', '20 Maj'],
        values: [73.5, 73.2, 73.0, 72.8, 72.7, 72.6, 72.5, 72.5]
      }
    }
  };

  const dashboardData = data || sampleData;
  updateSummaryStats(dashboardData.daily_stats);
  createActivityChart(dashboardData.charts.activity);
  createHeartRateChart(dashboardData.charts.heart_rate);
  createSleepChart(dashboardData.charts.sleep);
  createWeightChart(dashboardData.charts.weight);
}

function updateSummaryStats(stats) {
  // Kroki
  document.getElementById('dailySteps').textContent = stats.steps.toLocaleString();
  const stepsPercentage = Math.min(Math.round((stats.steps / stats.goal_steps) * 100), 100);
  document.getElementById('stepsProgress').style.width = `${stepsPercentage}%`;
  document.getElementById('stepsPercentage').textContent = `${stepsPercentage}%`;
  document.getElementById('stepsGoal').textContent = stats.goal_steps.toLocaleString();

  // Tętno
  document.getElementById('avgHeartRate').textContent = stats.avg_heart_rate;
  document.getElementById('restingHeartRate').textContent = stats.resting_heart_rate;
  document.getElementById('maxHeartRate').textContent = stats.max_heart_rate;

  // Sen
  document.getElementById('sleepDuration').textContent = formatSleepDuration(stats.sleep_hours);
  const sleepPercentage = Math.min(Math.round((stats.sleep_hours / stats.goal_sleep_hours) * 100), 100);
  document.getElementById('sleepProgress').style.width = `${sleepPercentage}%`;
  document.getElementById('sleepPercentage').textContent = `${sleepPercentage}%`;
  document.getElementById('sleepGoal').textContent = stats.goal_sleep_hours;

  // Waga
  document.getElementById('currentWeight').textContent = stats.weight;
  document.getElementById('bmiValue').textContent = `BMI: ${stats.bmi}`;

  const weightChangeText = stats.weight_change > 0
    ? `+${stats.weight_change} kg`
    : `${stats.weight_change} kg`;

  const weightChangeEl = document.getElementById('weightDifference');
  weightChangeEl.textContent = `Zmiana: ${weightChangeText}`;
  weightChangeEl.classList.remove('text-red-500', 'text-green-500', 'text-gray-500');
  weightChangeEl.classList.add(
    stats.weight_change < 0 ? 'text-green-500' :
    stats.weight_change > 0 ? 'text-red-500' : 'text-gray-500'
  );
}

function formatSleepDuration(hours) {
  const wholeHours = Math.floor(hours);
  const minutes = Math.round((hours - wholeHours) * 60);
  return `${wholeHours}h ${minutes}m`;
}

// ========================
// FUNKCJE WYKRESÓW
// ========================

function createActivityChart(data) {
  const ctx = document.getElementById('activityChart').getContext('2d');
  if (window.activityChart) window.activityChart.destroy();

  window.activityChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [
        {
          label: 'Kroki',
          data: data.steps,
          backgroundColor: 'rgba(16, 185, 129, 0.5)',
          borderColor: 'rgba(16, 185, 129, 1)',
          borderWidth: 1,
          yAxisID: 'y'
        },
        {
          label: 'Dystans (km)',
          data: data.distance,
          type: 'line',
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(59, 130, 246, 1)',
          tension: 0.2,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: {
          type: 'linear',
          position: 'left',
          title: { display: true, text: 'Kroki' }
        },
        y1: {
          type: 'linear',
          position: 'right',
          grid: { drawOnChartArea: false },
          title: { display: true, text: 'Dystans (km)' }
        }
      }
    }
  });
}

function createHeartRateChart(data) {
  const ctx = document.getElementById('heartRateChart').getContext('2d');
  if (window.heartRateChart) window.heartRateChart.destroy();

  window.heartRateChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [
        {
          label: 'Średnie tętno',
          data: data.avg,
          backgroundColor: 'rgba(236, 72, 153, 0.2)',
          borderColor: 'rgba(236, 72, 153, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(236, 72, 153, 1)',
          tension: 0.3,
          fill: true
        },
        {
          label: 'Maksymalne tętno',
          data: data.max,
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          borderColor: 'rgba(239, 68, 68, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(239, 68, 68, 1)',
          tension: 0.3,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: {
          beginAtZero: false,
          title: { display: true, text: 'Uderzenia/min' }
        }
      }
    }
  });
}

function createSleepChart(data) {
  const ctx = document.getElementById('sleepChart').getContext('2d');
  if (window.sleepChart) window.sleepChart.destroy();

  window.sleepChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [
        {
          label: 'Czas snu (h)',
          data: data.hours,
          backgroundColor: 'rgba(79, 70, 229, 0.5)',
          borderColor: 'rgba(79, 70, 229, 1)',
          borderWidth: 1,
          yAxisID: 'y'
        },
        {
          label: 'Jakość snu (%)',
          data: data.quality,
          type: 'line',
          backgroundColor: 'rgba(124, 58, 237, 0.2)',
          borderColor: 'rgba(124, 58, 237, 1)',
          borderWidth: 2,
          pointBackgroundColor: 'rgba(124, 58, 237, 1)',
          tension: 0.2,
          yAxisID: 'y1',
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: {
          beginAtZero: true,
          max: 10,
          title: { display: true, text: 'Godziny' }
        },
        y1: {
          type: 'linear',
          position: 'right',
          min: 0,
          max: 100,
          grid: { drawOnChartArea: false },
          title: { display: true, text: 'Jakość (%)' }
        }
      }
    }
  });
}

function createWeightChart(data) {
  const ctx = document.getElementById('weightChart').getContext('2d');
  if (window.weightChart) window.weightChart.destroy();

  window.weightChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Waga (kg)',
        data: data.values,
        backgroundColor: 'rgba(139, 92, 246, 0.2)',
        borderColor: 'rgba(139, 92, 246, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(139, 92, 246, 1)',
        tension: 0.3,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: {
          beginAtZero: false,
          suggestedMin: Math.min(...data.values) - 2,
          suggestedMax: Math.max(...data.values) + 2,
          title: { display: true, text: 'Waga (kg)' }
        }
      }
    }
  });
}