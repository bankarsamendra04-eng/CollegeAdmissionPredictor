document.addEventListener('DOMContentLoaded', () => {
  const collegeState = {
    colleges: [],
    currentPage: 1,
    totalColleges: 0,
    filters: {
      search: '',
      college_type: [],
      city: '',
      state: '',
      min_fees: null,
      max_fees: null,
      sort: 'ranking',
      page: 1,
      limit: 12
    }
  };

  let searchTimeout;

  const fetchColleges = async () => {
    try {
      const container = document.getElementById('colleges-grid') || document.getElementById('college-list-container');
      if (container) {
        container.innerHTML = `
          <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
            <i class="fas fa-spinner fa-spin fa-2x" style="color: var(--primary);"></i>
            <p style="margin-top: 1rem; color: var(--gray-500);">Loading colleges...</p>
          </div>`;
      }

      const queryParams = new URLSearchParams();
      if (collegeState.filters.search) queryParams.set('search', collegeState.filters.search);
      if (collegeState.filters.city) queryParams.set('city', collegeState.filters.city);
      if (collegeState.filters.state) queryParams.set('state', collegeState.filters.state);
      if (collegeState.filters.min_fees) queryParams.set('min_fees', collegeState.filters.min_fees);
      if (collegeState.filters.max_fees) queryParams.set('max_fees', collegeState.filters.max_fees);
      if (collegeState.filters.sort) queryParams.set('sort', collegeState.filters.sort);
      queryParams.set('page', collegeState.filters.page);
      queryParams.set('limit', collegeState.filters.limit);
      
      collegeState.filters.college_type.forEach(t => queryParams.append('college_type', t));
      
      const data = await apiFetch(`/api/colleges?${queryParams.toString()}`);
      collegeState.colleges = data.colleges || [];
      collegeState.totalColleges = data.total || 0;
      
      const countEl = document.getElementById('results-count');
      if (countEl) {
        const start = Math.min((collegeState.filters.page - 1) * collegeState.filters.limit + 1, collegeState.totalColleges);
        const end = Math.min(collegeState.filters.page * collegeState.filters.limit, collegeState.totalColleges);
        countEl.textContent = collegeState.totalColleges > 0 
          ? `Showing ${start}-${end} of ${collegeState.totalColleges} colleges` 
          : 'Showing 0 of 0 colleges';
      }

      renderCollegeCards(collegeState.colleges);
    } catch (err) {
      console.error(err);
      const container = document.getElementById('colleges-grid') || document.getElementById('college-list-container');
      if (container) {
        container.innerHTML = '<div class="alert alert-danger" style="grid-column:1/-1;">Failed to load colleges. Please try again.</div>';
      }
    }
  };

  const renderCollegeCards = (colleges) => {
    const container = document.getElementById('colleges-grid') || document.getElementById('college-list-container');
    if (!container) return;
    
    if (!colleges || colleges.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 4rem 1rem; background: #fff; border-radius: var(--radius-md); box-shadow: var(--shadow-sm);">
          <i class="fas fa-school fa-3x" style="color: var(--gray-300); margin-bottom: 1rem;"></i>
          <h3 style="color: var(--gray-700);">No colleges found</h3>
          <p style="color: var(--gray-500);">Try clearing some filters or searching with a different keyword.</p>
        </div>`;
      return;
    }

    container.innerHTML = colleges.map(c => {
      const fees = c.fees_per_year || c.fees || 0;
      const avgPkg = c.avg_package_lpa || c.avg_package || 0;
      const highestPkg = c.highest_package_lpa || c.highest_package || 0;
      const escapedName = (c.name || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');

      return `
        <div class="college-card">
          <div class="card-top" style="margin-bottom: 1rem;">
            <div class="card-header-info">
              <h3 class="college-name" style="font-size: 1.15rem; font-weight: 700; color: var(--gray-900);">${c.name}</h3>
              <div class="college-meta" style="color: var(--gray-500); font-size: 0.85rem; margin-top: 4px;">
                <span><i class="fas fa-map-marker-alt"></i> ${c.city || ''}, ${c.state || ''}</span>
              </div>
            </div>
            <div style="margin-top: 6px; display: flex; gap: 6px; flex-wrap: wrap;">
              <span class="badge" style="background:#e0e7ff; color:#3730a3; font-weight:600; padding:3px 8px; border-radius:4px; font-size:12px;">${c.college_type || 'Engineering'}</span>
              ${c.naac_grade ? `<span class="badge" style="background:#dcfce7; color:#166534; font-weight:600; padding:3px 8px; border-radius:4px; font-size:12px;">NAAC ${c.naac_grade}</span>` : ''}
              ${c.nba_accredited === 'Yes' ? `<span class="badge" style="background:#fef3c7; color:#92400e; font-weight:600; padding:3px 8px; border-radius:4px; font-size:12px;">NBA</span>` : ''}
            </div>
          </div>

          <div class="college-extras" style="display:grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 1.25rem; font-size: 0.9rem;">
            <div class="extra-item" style="background:var(--gray-50); padding:6px 10px; border-radius:6px;">
              <span style="font-size:11px; color:var(--gray-500); display:block;">Annual Fees</span>
              <strong>${formatCurrency(fees)}/yr</strong>
            </div>
            <div class="extra-item" style="background:var(--gray-50); padding:6px 10px; border-radius:6px;">
              <span style="font-size:11px; color:var(--gray-500); display:block;">Avg Package</span>
              <strong>${avgPkg ? avgPkg + ' LPA' : 'N/A'}</strong>
            </div>
            <div class="extra-item" style="background:var(--gray-50); padding:6px 10px; border-radius:6px;">
              <span style="font-size:11px; color:var(--gray-500); display:block;">Highest Package</span>
              <strong>${highestPkg ? highestPkg + ' LPA' : 'N/A'}</strong>
            </div>
            <div class="extra-item" style="background:var(--gray-50); padding:6px 10px; border-radius:6px;">
              <span style="font-size:11px; color:var(--gray-500); display:block;">Est. Year</span>
              <strong>${c.established_year || 'N/A'}</strong>
            </div>
          </div>

          <div class="card-actions" style="display:flex; gap:8px;">
            <button class="btn btn-sm btn-primary" style="flex:1;" onclick="showCollegeDetail(${c.id})">
              <i class="fas fa-info-circle"></i> Details
            </button>
            <button class="btn btn-sm btn-secondary" style="flex:1;" onclick="CompareModule.add({college_id:${c.id}, branch_id:null, name:'${escapedName}', branch:'All Branches'})">
              <i class="fas fa-balance-scale"></i> + Compare
            </button>
          </div>
        </div>
      `;
    }).join('');
  };

  const applyFilters = () => {
    collegeState.filters.page = 1;
    fetchColleges();
  };

  // Search input listeners (both sidebar-search and college-search)
  const searchInput = document.getElementById('sidebar-search') || document.getElementById('college-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      collegeState.filters.search = e.target.value.trim();
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(applyFilters, 350);
    });
  }

  // Type checkboxes
  document.querySelectorAll('.filter-type-checkbox, .filter-section input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      const checked = Array.from(document.querySelectorAll('.filter-section input[type="checkbox"]:checked'))
        .map(el => el.value)
        .filter(v => ['gov', 'gov_aided', 'autonomous', 'private', 'Government', 'Autonomous', 'Private'].includes(v));
      collegeState.filters.college_type = checked;
      applyFilters();
    });
  });

  // State / City dropdowns
  const citySelect = document.getElementById('filter-city');
  if (citySelect) {
    citySelect.addEventListener('change', (e) => {
      collegeState.filters.city = e.target.value;
      applyFilters();
    });
  }

  const stateSelect = document.getElementById('filter-state');
  if (stateSelect) {
    stateSelect.addEventListener('change', (e) => {
      collegeState.filters.state = e.target.value;
      applyFilters();
    });
  }

  // Fees inputs
  const minFeesInput = document.getElementById('min-fees');
  if (minFeesInput) {
    minFeesInput.addEventListener('change', (e) => {
      collegeState.filters.min_fees = e.target.value ? parseInt(e.target.value) : null;
      applyFilters();
    });
  }

  const maxFeesInput = document.getElementById('max-fees');
  if (maxFeesInput) {
    maxFeesInput.addEventListener('change', (e) => {
      collegeState.filters.max_fees = e.target.value ? parseInt(e.target.value) : null;
      applyFilters();
    });
  }

  // Sort
  const sortSelect = document.getElementById('college-sort');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      collegeState.filters.sort = e.target.value;
      applyFilters();
    });
  }

  // Apply button
  const applyBtn = document.getElementById('apply-filters');
  if (applyBtn) {
    applyBtn.addEventListener('click', applyFilters);
  }

  // Initial load
  fetchColleges();

  // Detail Modal
  window.showCollegeDetail = async (collegeId) => {
    try {
      const data = await apiFetch(`/api/college/${collegeId}`);
      const placement = data.placements?.[0] || {};
      const branches = data.branches || [];

      let html = `
        <h2 style="color: var(--primary); margin-bottom: 8px;">${data.name}</h2>
        <div style="color: var(--gray-500); margin-bottom: 16px; font-size: 14px;">
          <span><i class="fas fa-map-marker-alt"></i> ${data.city}, ${data.state}</span> | 
          <span><i class="fas fa-university"></i> ${data.college_type}</span> |
          <span>University: ${data.university || 'Affiliated'}</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px;">
          <div style="background:var(--gray-50); padding:10px; border-radius:8px;">
            <span style="font-size:11px; color:var(--gray-500); display:block;">ANNUAL FEES</span>
            <strong style="font-size:16px;">₹${(data.fees_per_year || 0).toLocaleString()}/yr</strong>
          </div>
          <div style="background:var(--gray-50); padding:10px; border-radius:8px;">
            <span style="font-size:11px; color:var(--gray-500); display:block;">AVG PACKAGE</span>
            <strong style="font-size:16px;">${data.avg_package_lpa || 'N/A'} LPA</strong>
          </div>
          <div style="background:var(--gray-50); padding:10px; border-radius:8px;">
            <span style="font-size:11px; color:var(--gray-500); display:block;">HIGHEST PACKAGE</span>
            <strong style="font-size:16px;">${data.highest_package_lpa || 'N/A'} LPA</strong>
          </div>
          <div style="background:var(--gray-50); padding:10px; border-radius:8px;">
            <span style="font-size:11px; color:var(--gray-500); display:block;">NAAC GRADE</span>
            <strong style="font-size:16px;">${data.naac_grade || 'N/A'}</strong>
          </div>
          <div style="background:var(--gray-50); padding:10px; border-radius:8px;">
            <span style="font-size:11px; color:var(--gray-500); display:block;">PLACEMENT %</span>
            <strong style="font-size:16px;">${placement.placement_percentage ? placement.placement_percentage + '%' : 'N/A'}</strong>
          </div>
        </div>

        <h3 style="margin-bottom: 12px; font-size: 16px; color: var(--gray-900);">Available Branches (${branches.length})</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;">
          ${branches.map(b => `<span style="background:#e0e7ff; color:#3730a3; padding:5px 10px; border-radius:6px; font-size:13px; font-weight:500;">${b.branch_name} (${b.total_seats} seats)</span>`).join('')}
        </div>
      `;
      showModal(html, 'College Details');
    } catch (e) {
      console.error(e);
      showToast('Could not load college details', 'error');
    }
  };
});
