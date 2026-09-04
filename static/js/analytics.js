document.addEventListener('DOMContentLoaded', async () => {
  if (typeof Chart === 'undefined') {
    console.error('Chart.js is required for analytics');
    return;
  }

  let trendChartInstance = null;
  let branchChartInstance = null;
  let typeChartInstance = null;
  let scatterChartInstance = null;

  const loadAnalytics = async () => {
    try {
      const categorySelect = document.getElementById('analytics-category');
      const category = categorySelect ? categorySelect.value : 'OPEN';

      const data = await apiFetch(`/api/analytics?category=${encodeURIComponent(category)}`);
      
      if (data.cutoff_trends) renderCutoffTrendChart(data.cutoff_trends);
      if (data.branch_demand) renderBranchDemandChart(data.branch_demand);
      if (data.category_distribution) renderCollegeTypePieChart(data.category_distribution);
      if (data.top_colleges) renderPackageScatterChart(data.top_colleges);
      if (data.cutoff_trends) renderCutoffTable(data.cutoff_trends);
      
    } catch (err) {
      console.error('Failed to load analytics', err);
    }
  };

  const applyBtn = document.getElementById('update-analytics');
  if (applyBtn) {
    applyBtn.addEventListener('click', (e) => {
      e.preventDefault();
      loadAnalytics();
    });
  }

  const categorySelect = document.getElementById('analytics-category');
  if (categorySelect) {
    categorySelect.addEventListener('change', loadAnalytics);
  }

  function renderCutoffTrendChart(trends) {
    const ctx = document.getElementById('cutoffTrendChart') || document.getElementById('trendChart');
    if (!ctx) return;
    
    if (trendChartInstance) {
      trendChartInstance.destroy();
    }

    const grouped = {};
    const years = new Set();
    
    trends.forEach(t => {
      years.add(t.year);
      const key = `${t.name} (${t.branch})`;
      if (!grouped[key]) grouped[key] = {};
      grouped[key][t.year] = t.closing_rank;
    });
    
    const labels = Array.from(years).sort();
    const datasets = Object.keys(grouped).slice(0, 6).map((key, i) => {
      const colors = ['#2563eb', '#16a34a', '#dc2626', '#d97706', '#0891b2', '#7c3aed'];
      return {
        label: key,
        data: labels.map(y => grouped[key][y] || null),
        borderColor: colors[i % colors.length],
        backgroundColor: colors[i % colors.length],
        fill: false,
        tension: 0.2
      };
    });

    trendChartInstance = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { 
            reverse: true,
            title: { display: true, text: 'Closing Rank (Lower = Tougher)' }
          },
          x: { title: { display: true, text: 'Admission Year' } }
        },
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  }

  function renderBranchDemandChart(data) {
    const ctx = document.getElementById('branchDemandChart') || document.getElementById('branchChart');
    if (!ctx) return;
    
    if (branchChartInstance) {
      branchChartInstance.destroy();
    }

    const labels = data.slice(0, 8).map(d => d.branch);
    const avgRanks = data.slice(0, 8).map(d => Math.round(d.avg_closing_rank));

    branchChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Avg Closing Rank',
          data: avgRanks,
          backgroundColor: '#2563eb',
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { reverse: true, title: { display: true, text: 'Avg Closing Rank' } }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  function renderCollegeTypePieChart(data) {
    const ctx = document.getElementById('collegeTypeChart') || document.getElementById('typeChart');
    if (!ctx) return;
    
    if (typeChartInstance) {
      typeChartInstance.destroy();
    }

    typeChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: data.map(d => d.category),
        datasets: [{
          data: data.map(d => d.count),
          backgroundColor: ['#2563eb', '#16a34a', '#d97706', '#dc2626', '#64748b']
        }]
      },
      options: { 
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  }

  function renderPackageScatterChart(data) {
    const ctx = document.getElementById('packageScatterChart') || document.getElementById('scatterChart');
    if (!ctx) return;
    
    if (scatterChartInstance) {
      scatterChartInstance.destroy();
    }

    const points = data.map(d => ({
      x: d.placement_pct || 75,
      y: d.avg_package || 6.0,
      name: d.name
    }));

    scatterChartInstance = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Colleges',
          data: points,
          backgroundColor: '#2563eb',
          pointRadius: 6,
          pointHoverRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.raw.name}: Avg ₹${ctx.raw.y} LPA (${ctx.raw.x}% Placed)`
            }
          }
        },
        scales: {
          x: { title: { display: true, text: 'Placement %' }, min: 50, max: 100 },
          y: { title: { display: true, text: 'Avg Package (LPA)' } }
        }
      }
    });
  }

  function renderCutoffTable(data) {
    const container = document.getElementById('analytics-table-container') || document.getElementById('analytics-table');
    if (!container) return;
    
    let html = `
      <table class="data-table" style="width:100%; border-collapse:collapse;">
        <thead>
          <tr style="background:var(--gray-100);">
            <th style="padding:10px; text-align:left;">College</th>
            <th style="padding:10px; text-align:left;">Branch</th>
            <th style="padding:10px; text-align:center;">Year</th>
            <th style="padding:10px; text-align:center;">Category</th>
            <th style="padding:10px; text-align:right;">Closing Rank</th>
          </tr>
        </thead>
        <tbody>
    `;
    
    data.slice(0, 30).forEach(row => {
      html += `
        <tr style="border-bottom:1px solid var(--gray-200);">
          <td style="padding:10px; font-weight:600;">${row.name}</td>
          <td style="padding:10px;">${row.branch}</td>
          <td style="padding:10px; text-align:center;">${row.year}</td>
          <td style="padding:10px; text-align:center;"><span class="badge" style="background:#e0e7ff; color:#3730a3; padding:2px 6px; border-radius:4px;">${row.category}</span></td>
          <td style="padding:10px; text-align:right; font-weight:700; color:var(--primary);">${(row.closing_rank || 0).toLocaleString()}</td>
        </tr>
      `;
    });
    
    html += '</tbody></table>';
    
    if (container.tagName === 'TABLE') {
      container.parentElement.innerHTML = `<div id="analytics-table-container" class="table-responsive">${html}</div>`;
    } else {
      container.innerHTML = html;
    }
  }

  // Initial load
  loadAnalytics();
});
