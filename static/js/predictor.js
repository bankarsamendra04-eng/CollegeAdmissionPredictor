/**
 * predictor.js — Multi-step prediction form logic
 * Handles form state, validation, API calls, and result rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
  // ─── State ────────────────────────────────────────────────────────────────
  const formState = {
    step: 1,
    qualification: '12th',
    entrance_exam: 'mht-cet',
    merit_rank: 5000,
    category_rank: null,
    percentile: 90.0,
    entrance_score: null,
    twelfth_percentage: null,
    diploma_percentage: null,
    cgpa: null,
    home_university: 'pune',
    domicile_state: 'maharashtra',
    category: 'OPEN',
    gender: 'MALE',
    preferred_branches: ['CSE', 'IT'],
    college_type: 'Any',
    preferred_state: 'Maharashtra',
    preferred_cities: [],
    no_location_preference: true
  };

  const STEPS = 5;
  let predictionData = null;
  let allColleges = [];

  // ─── DOM References ────────────────────────────────────────────────────────
  const formWrapper    = document.getElementById('prediction-form-wrapper');
  const resultsSection = document.getElementById('results-section');
  const loadingAnim    = document.getElementById('loading-animation');
  const resultDash     = document.getElementById('result-dashboard');

  // ─── Step Navigation ──────────────────────────────────────────────────────
  const showStep = (n) => {
    formState.step = n;
    for (let i = 1; i <= STEPS; i++) {
      const el = document.getElementById(`step-${i}`);
      if (el) el.classList.toggle('active', i === n);
    }
    updateProgressBar(n);
    if (n === STEPS) buildReviewHTML();
  };

  const updateProgressBar = (step) => {
    const items = document.querySelectorAll('#prediction-progress li');
    items.forEach((item, idx) => {
      item.classList.toggle('active', idx + 1 === step);
      item.classList.toggle('completed', idx + 1 < step);
    });
  };

  // ─── Read All Form Inputs from DOM ─────────────────────────────────────────
  const readCurrentFormData = () => {
    // Step 1
    const qualEl = document.getElementById('qualification');
    const examEl = document.getElementById('entrance_exam');
    if (qualEl && qualEl.value) formState.qualification = qualEl.value;
    if (examEl && examEl.value) formState.entrance_exam = examEl.value;

    // Step 2
    const rankEl = document.getElementById('merit_rank');
    const percEl = document.getElementById('entrance_percentile');
    const scoreEl = document.getElementById('entrance_score');
    const hscEl = document.getElementById('hsc_percentage');
    const dipEl = document.getElementById('diploma_score');
    const catRankEl = document.getElementById('category_rank');
    const homeUniEl = document.getElementById('home_university');
    const domStateEl = document.getElementById('domicile_state');

    if (rankEl && rankEl.value) formState.merit_rank = parseInt(rankEl.value, 10);
    if (percEl && percEl.value !== '') formState.percentile = parseFloat(percEl.value);
    if (scoreEl && scoreEl.value !== '') formState.entrance_score = parseFloat(scoreEl.value);
    if (hscEl && hscEl.value !== '') formState.twelfth_percentage = parseFloat(hscEl.value);
    if (dipEl && dipEl.value !== '') formState.diploma_percentage = parseFloat(dipEl.value);
    if (catRankEl && catRankEl.value !== '') formState.category_rank = parseInt(catRankEl.value, 10);
    if (homeUniEl && homeUniEl.value) formState.home_university = homeUniEl.value;
    if (domStateEl && domStateEl.value) formState.domicile_state = domStateEl.value;

    // Step 3
    const catRadio = document.querySelector('input[name="category"]:checked');
    const genRadio = document.querySelector('input[name="gender"]:checked');
    if (catRadio && catRadio.value) {
      let cVal = catRadio.value.toUpperCase();
      if (cVal === 'VJDT') cVal = 'VJ';
      formState.category = cVal;
    }
    if (genRadio && genRadio.value) formState.gender = genRadio.value.toUpperCase();

    // Step 4
    const checkedBranches = Array.from(document.querySelectorAll('input[name="branches"]:checked'))
      .map(cb => {
        const val = cb.value.toUpperCase();
        if (val === 'ELEC') return 'EE';
        return val;
      });
    formState.preferred_branches = checkedBranches;

    const ctypeRadio = document.querySelector('input[name="college_type"]:checked');
    formState.college_type = ctypeRadio ? ctypeRadio.value : 'Any';

    const citiesSelect = document.getElementById('pref_cities');
    if (citiesSelect) {
      formState.preferred_cities = Array.from(citiesSelect.selectedOptions).map(o => {
        return o.value.charAt(0).toUpperCase() + o.value.slice(1);
      });
    }

    const noLoc = document.getElementById('no_loc_pref');
    formState.no_location_preference = noLoc ? noLoc.checked : false;
    if (formState.no_location_preference) formState.preferred_cities = [];
  };

  // ─── Validation ───────────────────────────────────────────────────────────
  const showFieldError = (fieldId, msg) => {
    const el = document.getElementById(fieldId);
    if (!el) return;
    el.parentNode.querySelectorAll('.field-error').forEach(e => e.remove());
    const err = document.createElement('div');
    err.className = 'field-error';
    err.style.cssText = 'color: #dc2626; font-size: 13px; margin-top: 4px; font-weight: 500;';
    err.textContent = msg;
    el.parentNode.appendChild(err);
    el.classList.add('input-error');
  };

  const clearErrors = () => {
    document.querySelectorAll('.field-error').forEach(e => e.remove());
    document.querySelectorAll('.input-error').forEach(e => e.classList.remove('input-error'));
  };

  const validateStep = (n) => {
    clearErrors();
    readCurrentFormData();
    let valid = true;

    if (n === 1) {
      if (!formState.qualification) { showFieldError('qualification', 'Please select your qualification.'); valid = false; }
      if (!formState.entrance_exam) { showFieldError('entrance_exam', 'Please select your entrance exam.'); valid = false; }

    } else if (n === 2) {
      if (!formState.merit_rank || formState.merit_rank <= 0 || isNaN(formState.merit_rank)) {
        showFieldError('merit_rank', 'Please enter a valid positive merit rank.');
        valid = false;
      }
      if (formState.percentile !== null && !isNaN(formState.percentile) && (formState.percentile < 0 || formState.percentile > 100)) {
        showFieldError('entrance_percentile', 'Percentile must be between 0 and 100.');
        valid = false;
      }

    } else if (n === 3) {
      if (!formState.category) { valid = false; }

    } else if (n === 4) {
      if (!formState.preferred_branches || formState.preferred_branches.length === 0) {
        const branchGrid = document.querySelector('.checkbox-grid');
        if (branchGrid) {
          const err = document.createElement('div');
          err.className = 'field-error';
          err.style.cssText = 'color: #dc2626; font-size: 13px; margin-top: 4px; font-weight: 500;';
          err.textContent = 'Please select at least one preferred branch.';
          branchGrid.parentNode.appendChild(err);
        }
        valid = false;
      }
    }

    return valid;
  };

  // ─── Step Controls ────────────────────────────────────────────────────────
  window.nextStep = () => {
    if (validateStep(formState.step) && formState.step < STEPS) {
      showStep(formState.step + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  window.prevStep = () => {
    if (formState.step > 1) {
      showStep(formState.step - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  // ─── Review Summary ───────────────────────────────────────────────────────
  const buildReviewHTML = () => {
    readCurrentFormData();
    const reviewDiv = document.getElementById('summary-container');
    if (!reviewDiv) return;

    const branchesText = (formState.preferred_branches && formState.preferred_branches.length > 0)
      ? formState.preferred_branches.join(', ')
      : '<span style="color:#dc2626;">None selected</span>';

    const rankText = formState.merit_rank ? Number(formState.merit_rank).toLocaleString() : '<span style="color:#dc2626;">Not entered</span>';
    const percentileText = formState.percentile !== null && !isNaN(formState.percentile) ? `${formState.percentile}%` : 'N/A';

    reviewDiv.innerHTML = `
      <div class="card" style="border: 1px solid var(--gray-200); padding: 1.5rem; border-radius: var(--radius-md); margin-top: 1rem;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; font-size: 14px;">
          <div><strong style="color:var(--gray-500); display:block; font-size:12px; text-transform:uppercase;">Entrance Exam</strong> <span>${formState.entrance_exam || 'MHT-CET'}</span></div>
          <div><strong style="color:var(--gray-500); display:block; font-size:12px; text-transform:uppercase;">Qualification</strong> <span>${formState.qualification || '12th'}</span></div>
          <div><strong style="color:var(--gray-500); display:block; font-size:12px; text-transform:uppercase;">Merit Rank</strong> <span style="font-size:16px; font-weight:700; color:var(--primary);">${rankText}</span></div>
          <div><strong style="color:var(--gray-500); display:block; font-size:12px; text-transform:uppercase;">Percentile</strong> <span>${percentileText}</span></div>
          <div><strong style="color:var(--gray-500); display:block; font-size:12px; text-transform:uppercase;">Category</strong> <span class="badge" style="background:#e0e7ff; color:#3730a3; padding:2px 8px; border-radius:4px; font-weight:600;">${formState.category || 'OPEN'}</span></div>
          <div><strong style="color:var(--gray-500); display:block; font-size:12px; text-transform:uppercase;">Gender</strong> <span>${formState.gender || 'MALE'}</span></div>
          <div><strong style="color:var(--gray-500); display:block; font-size:12px; text-transform:uppercase;">College Type</strong> <span>${formState.college_type || 'Any'}</span></div>
          <div style="grid-column: 1 / -1;"><strong style="color:var(--gray-500); display:block; font-size:12px; text-transform:uppercase;">Preferred Branches</strong> <span style="font-weight:600; color:var(--gray-900);">${branchesText}</span></div>
          ${formState.preferred_cities && formState.preferred_cities.length ? `<div style="grid-column: 1 / -1;"><strong style="color:var(--gray-500); display:block; font-size:12px; text-transform:uppercase;">Preferred Cities</strong> <span>${formState.preferred_cities.join(', ')}</span></div>` : ''}
        </div>
      </div>
    `;
  };

  // ─── Prediction Submission ────────────────────────────────────────────────
  window.submitPrediction = async () => {
    readCurrentFormData();

    // Check required fields
    if (!formState.merit_rank || formState.merit_rank <= 0 || isNaN(formState.merit_rank)) {
      if (typeof showToast === 'function') showToast('Please enter a valid Merit Rank in Step 2.', 'warning');
      showStep(2);
      document.getElementById('merit_rank')?.focus();
      return;
    }

    if (!formState.preferred_branches || formState.preferred_branches.length === 0) {
      if (typeof showToast === 'function') showToast('Please select at least one preferred branch in Step 4.', 'warning');
      showStep(4);
      return;
    }

    if (!formWrapper || !resultsSection || !loadingAnim) return;

    formWrapper.style.display = 'none';
    resultsSection.classList.remove('hidden');
    loadingAnim.classList.remove('hidden');
    if (resultDash) resultDash.classList.add('hidden');

    // Quick loading animation checklist
    const loadingItems = document.querySelectorAll('.loading-steps li');
    let delay = 0;
    loadingItems.forEach((item, idx) => {
      setTimeout(() => {
        item.classList.remove('pending');
        item.classList.add('completed');
        item.innerHTML = `<i class="fas fa-check-circle" style="color:var(--success);"></i> ${item.textContent}`;
      }, idx * 200);
      delay = (idx + 1) * 200;
    });

    // Build API payload
    const payload = {
      merit_rank: formState.merit_rank,
      category_rank: formState.category_rank,
      percentile: formState.percentile,
      entrance_score: formState.entrance_score,
      category: formState.category || 'OPEN',
      gender: formState.gender || 'MALE',
      twelfth_percentage: formState.twelfth_percentage,
      diploma_percentage: formState.diploma_percentage,
      preferred_branches: formState.preferred_branches,
      college_type: formState.college_type || 'Any',
      preferred_city: formState.preferred_cities || [],
      entrance_exam: formState.entrance_exam || 'MHT-CET',
    };

    try {
      const data = await apiFetch('/api/predict', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      predictionData = data;

      setTimeout(() => {
        loadingAnim.classList.add('hidden');
        if (resultDash) {
          resultDash.classList.remove('hidden');
          renderResults(data);
          resultDash.scrollIntoView({ behavior: 'smooth' });
        }
      }, Math.max(delay, 500));

    } catch (err) {
      console.error('Prediction submit error:', err);
      loadingAnim.classList.add('hidden');
      formWrapper.style.display = 'block';
      resultsSection.classList.add('hidden');
      if (typeof showToast === 'function') {
        showToast('Prediction failed. Please check your inputs and try again.', 'error');
      }
    }
  };

  // ─── Results Rendering ────────────────────────────────────────────────────
  const renderResults = (data) => {
    allColleges = data.recommendations || [];

    // Update summary cards
    const recCount = document.getElementById('rec-count');
    const bestCollege = document.getElementById('best-college');
    const bestBranch = document.getElementById('best-branch');
    if (recCount) recCount.textContent = allColleges.length;
    if (bestCollege) bestCollege.textContent = data.best_college || 'N/A';
    if (bestBranch) bestBranch.textContent = data.best_branch || 'N/A';

    // Update outlook arc score
    const scoreText = document.querySelector('.score-text');
    const arcVal = document.querySelector('.arc-val');
    if (scoreText && data.overall_outlook) {
      const score = data.overall_outlook.score || 0;
      scoreText.textContent = `${score.toFixed(0)}%`;
      if (arcVal) {
        const offset = Math.max(0, 125 - (score / 100) * 125);
        arcVal.style.strokeDashoffset = offset;
        arcVal.style.stroke = score >= 75 ? '#16a34a' : score >= 40 ? '#d97706' : '#dc2626';
      }
    }

    setupResultFilters();
    renderCollegeCards(allColleges);
    setupComparePanel();
  };

  // ─── College Cards ────────────────────────────────────────────────────────
  const renderCollegeCards = (colleges) => {
    const grid = document.getElementById('predictions-grid');
    if (!grid) return;

    if (!colleges || colleges.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 4rem 1rem; background: #fff; border-radius: var(--radius-md); box-shadow: var(--shadow-sm);">
          <i class="fas fa-search fa-3x" style="color:var(--gray-300); margin-bottom: 1rem;"></i>
          <h3 style="color: var(--gray-700);">No colleges match the selected filter</h3>
          <p style="color: var(--gray-500);">Try selecting "All" or searching with a different term.</p>
        </div>`;
      return;
    }

    grid.innerHTML = colleges.map((c) => {
      const cls = c.classification || 'UNLIKELY';
      const clsConfig = {
        SAFE: { label: '🟢 SAFE', bg: '#dcfce7', color: '#166534', border: '#16a34a' },
        MODERATE: { label: '🟡 MODERATE', bg: '#fef3c7', color: '#92400e', border: '#d97706' },
        DREAM: { label: '🔴 DREAM', bg: '#fee2e2', color: '#991b1b', border: '#dc2626' },
        UNLIKELY: { label: '⚪ UNLIKELY', bg: '#f1f5f9', color: '#475569', border: '#64748b' }
      }[cls] || { label: cls, bg: '#f1f5f9', color: '#475569', border: '#64748b' };

      const prob = c.probability || 0;
      const probBarColor = prob >= 75 ? '#16a34a' : prob >= 40 ? '#d97706' : '#dc2626';

      const rankGap = c.rank_gap;
      const rankGapText = rankGap > 0
        ? `<span style="color:#16a34a; font-weight:600;">▲ Ahead by ${rankGap.toLocaleString()}</span>`
        : rankGap < 0
        ? `<span style="color:#dc2626; font-weight:600;">▼ Behind by ${Math.abs(rankGap).toLocaleString()}</span>`
        : `<span style="color:var(--gray-500); font-weight:600;">= Exact Match</span>`;

      const fees = c.fees ? (typeof formatCurrency === 'function' ? formatCurrency(c.fees) : `₹${c.fees.toLocaleString()}`) : 'N/A';
      const avgPkg = c.avg_package ? `${c.avg_package} LPA` : 'N/A';
      const escapedName = (c.college_name || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
      const escapedBranch = (c.branch || '').replace(/'/g, "\\'");
      const escapedExpl = (c.explanation || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');

      return `
        <div class="college-card" style="border-top: 4px solid ${clsConfig.border}; background: #fff; padding: 1.5rem; border-radius: var(--radius-md); box-shadow: var(--shadow-sm);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <div>
              <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--gray-900); margin-bottom: 4px;">${c.college_name || ''}</h3>
              <div style="font-size: 0.85rem; color: var(--gray-500);">
                <span><i class="fas fa-map-marker-alt"></i> ${c.city || ''}</span> | 
                <span><i class="fas fa-university"></i> ${c.college_type || ''}</span>
              </div>
            </div>
            <span style="background: ${clsConfig.bg}; color: ${clsConfig.color}; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 12px; white-space: nowrap;">${clsConfig.label}</span>
          </div>

          <div style="background: #e0e7ff; color: #3730a3; padding: 4px 10px; border-radius: 4px; font-size: 13px; font-weight: 600; display: inline-block; margin-bottom: 1rem;">
            <i class="fas fa-code-branch"></i> ${c.branch || ''}
          </div>

          <div style="margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
              <span style="color: var(--gray-500);">Admission Probability</span>
              <strong style="color: ${probBarColor}; font-size: 15px;">${prob.toFixed(1)}%</strong>
            </div>
            <div style="background: var(--gray-200); height: 8px; border-radius: 4px; overflow: hidden;">
              <div style="width: ${prob}%; height: 100%; background: ${probBarColor}; transition: width 0.8s ease;"></div>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px; background: var(--gray-50); padding: 10px; border-radius: 6px; margin-bottom: 1rem;">
            <div>
              <span style="color: var(--gray-500); display:block;">Prev Closing</span>
              <strong style="font-size: 14px;">${c.closing_rank_prev ? c.closing_rank_prev.toLocaleString() : 'N/A'}</strong>
            </div>
            <div>
              <span style="color: var(--gray-500); display:block;">Rank Difference</span>
              <span style="font-size: 13px;">${rankGapText}</span>
            </div>
            <div>
              <span style="color: var(--gray-500); display:block;">Annual Fees</span>
              <strong>${fees}</strong>
            </div>
            <div>
              <span style="color: var(--gray-500); display:block;">Avg Package</span>
              <strong>${avgPkg}</strong>
            </div>
          </div>

          <div style="display: flex; gap: 6px;">
            <button class="btn btn-sm btn-primary" style="flex:1;" onclick="showCollegeDetail(${c.college_id})">
              <i class="fas fa-info-circle"></i> Details
            </button>
            <button class="btn btn-sm btn-secondary" style="flex:1;" onclick="addToCompare(${c.college_id}, ${c.branch_id || 0}, '${escapedName}', '${escapedBranch}')">
              <i class="fas fa-balance-scale"></i> + Compare
            </button>
            <button class="btn btn-sm btn-outline" style="padding: 0 10px;" onclick="showWhyModal('${escapedExpl}')" title="Why is this recommended?">
              <i class="fas fa-question-circle"></i>
            </button>
          </div>
        </div>`;
    }).join('');
  };

  // ─── Filters ──────────────────────────────────────────────────────────────
  const setupResultFilters = () => {
    const searchInput = document.getElementById('search-college');
    const sortSelect  = document.getElementById('sort-results');
    const filterBtns  = document.querySelectorAll('.filter-btn');

    let activeFilter = 'all';

    const applyFilters = () => {
      let filtered = [...allColleges];
      const search = searchInput?.value.toLowerCase().trim() || '';

      if (search) {
        filtered = filtered.filter(c =>
          (c.college_name || '').toLowerCase().includes(search) ||
          (c.branch || '').toLowerCase().includes(search) ||
          (c.city || '').toLowerCase().includes(search)
        );
      }

      if (activeFilter !== 'all') {
        filtered = filtered.filter(c => (c.classification || '').toUpperCase() === activeFilter.toUpperCase());
      }

      const sort = sortSelect?.value || 'probability';
      if (sort === 'probability') filtered.sort((a, b) => b.probability - a.probability);
      else if (sort === 'rank') filtered.sort((a, b) => (a.closing_rank_prev || 99999) - (b.closing_rank_prev || 99999));
      else if (sort === 'fees') filtered.sort((a, b) => (a.fees || 999999) - (b.fees || 999999));

      renderCollegeCards(filtered);
    };

    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeFilter = btn.dataset.filter || 'all';
        applyFilters();
      });
    });

    searchInput?.addEventListener('input', applyFilters);
    sortSelect?.addEventListener('change', applyFilters);
  };

  // ─── Compare ──────────────────────────────────────────────────────────────
  let compareList = [];

  const setupComparePanel = () => {
    const panel = document.getElementById('comparison-panel');
    const closeBtn = panel?.querySelector('.close-panel');
    const compareNowBtn = document.getElementById('btn-compare-now');

    closeBtn?.addEventListener('click', () => panel?.classList.remove('open'));
    compareNowBtn?.addEventListener('click', openCompareModal);
  };

  window.addToCompare = (collegeId, branchId, name, branch) => {
    if (compareList.find(c => c.college_id === collegeId)) {
      if (typeof showToast === 'function') showToast('Already in comparison list.', 'info');
      return;
    }
    if (compareList.length >= 4) {
      if (typeof showToast === 'function') showToast('Maximum 4 colleges can be compared.', 'warning');
      return;
    }
    compareList.push({ college_id: collegeId, branch_id: branchId, name, branch });
    updateComparePanel();
    if (typeof showToast === 'function') showToast(`${name} added to comparison.`, 'success');
  };

  const updateComparePanel = () => {
    const panel = document.getElementById('comparison-panel');
    const list  = document.getElementById('compare-list');
    const count = document.getElementById('compare-count');
    if (!panel || !list) return;

    if (compareList.length > 0) panel.classList.add('open');
    if (count) count.textContent = compareList.length;

    list.innerHTML = compareList.map((c, i) => `
      <div class="compare-item" style="display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid var(--gray-200);">
        <span style="font-size:13px; font-weight:500;">${c.name} <small style="color:var(--gray-500);">(${c.branch})</small></span>
        <button onclick="removeFromCompare(${i})" style="background:none; border:none; color:#dc2626; cursor:pointer;"><i class="fas fa-times"></i></button>
      </div>`).join('');
  };

  window.removeFromCompare = (idx) => {
    compareList.splice(idx, 1);
    updateComparePanel();
    if (compareList.length === 0) {
      document.getElementById('comparison-panel')?.classList.remove('open');
    }
  };

  const openCompareModal = async () => {
    if (compareList.length < 2) {
      if (typeof showToast === 'function') showToast('Select at least 2 colleges to compare.', 'info');
      return;
    }
    try {
      const data = await apiFetch('/api/compare', {
        method: 'POST',
        body: JSON.stringify({
          college_ids: compareList.map(c => c.college_id),
          branch_ids:  compareList.map(c => c.branch_id),
          category: formState.category || 'OPEN',
        }),
      });
      renderCompareModal(data.colleges || []);
    } catch (e) {
      if (typeof showToast === 'function') showToast('Could not load comparison data.', 'error');
    }
  };

  const renderCompareModal = (colleges) => {
    const rows = [
      { label: 'College Type', key: 'college_type', higherBetter: false, isText: true },
      { label: 'City', key: 'city', higherBetter: false, isText: true },
      { label: 'Annual Fees (₹)', key: 'fees', higherBetter: false },
      { label: 'Closing Rank', key: 'closing_rank', higherBetter: false },
      { label: 'Avg Package (LPA)', key: 'avg_package', higherBetter: true },
      { label: 'Highest Pkg (LPA)', key: 'highest_package', higherBetter: true },
      { label: 'Placement %', key: 'placement_pct', higherBetter: true },
      { label: 'NAAC Grade', key: 'naac_grade', higherBetter: false, isText: true },
    ];

    const getHighlight = (values, higherBetter) => {
      const nums = values.map(v => parseFloat(v) || 0);
      const best = higherBetter ? Math.max(...nums) : Math.min(...nums.filter(n => n > 0));
      return nums.map(n => n === best ? 'background:#d1fae5; font-weight:700;' : '');
    };

    const header = `<tr style="background:var(--gray-100);"><th style="padding:10px; text-align:left;">Feature</th>${colleges.map(c => `<th style="padding:10px; text-align:center;">${c.name}<br><small style="color:var(--gray-500);">${c.branch || ''}</small></th>`).join('')}</tr>`;
    
    const rowsHTML = rows.map(row => {
      const vals = colleges.map(c => c[row.key]);
      const styles = row.isText ? vals.map(() => '') : getHighlight(vals, row.higherBetter);
      const cells = colleges.map((c, i) => {
        let val = c[row.key];
        if (val === null || val === undefined) val = 'N/A';
        else if (row.key === 'fees') val = `₹${Number(val).toLocaleString()}`;
        else if (row.key === 'avg_package' || row.key === 'highest_package') val = `${val} LPA`;
        else if (row.key === 'placement_pct') val = val !== 'N/A' ? `${val}%` : 'N/A';
        return `<td style="padding:10px; text-align:center; border-bottom:1px solid var(--gray-200); ${styles[i]}">${val}</td>`;
      }).join('');
      return `<tr><td style="padding:10px; font-weight:600; border-bottom:1px solid var(--gray-200);">${row.label}</td>${cells}</tr>`;
    }).join('');

    const html = `
      <h2 style="margin-bottom:16px; color:var(--primary);">College Comparison</h2>
      <div style="overflow-x:auto;">
        <table class="compare-table" style="width:100%; border-collapse:collapse;">
          <thead>${header}</thead>
          <tbody>${rowsHTML}</tbody>
        </table>
      </div>`;

    if (typeof showModal === 'function') showModal(html, 'College Comparison');
  };

  // ─── College Detail Modal ─────────────────────────────────────────────────
  window.showCollegeDetail = async (collegeId) => {
    try {
      const data = await apiFetch(`/api/college/${collegeId}`);
      const placement = data.placements?.[0] || {};

      const html = `
        <h2 style="color:var(--primary); margin-bottom:8px;">${data.name || 'College Details'}</h2>
        <div style="color:var(--gray-500); margin-bottom:16px; font-size:14px;">
          <span><i class="fas fa-map-marker-alt"></i> ${data.city || ''}, ${data.state || ''}</span> | 
          <span><i class="fas fa-university"></i> ${data.college_type || ''}</span>
          ${data.naac_grade ? ` | <span><i class="fas fa-award"></i> NAAC ${data.naac_grade}</span>` : ''}
        </div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:10px; margin-bottom:20px;">
          <div style="background:var(--gray-50); padding:10px; border-radius:6px;"><span style="font-size:11px; color:var(--gray-500); display:block;">ANNUAL FEES</span><strong>₹${Number(data.fees_per_year || 0).toLocaleString()}/yr</strong></div>
          <div style="background:var(--gray-50); padding:10px; border-radius:6px;"><span style="font-size:11px; color:var(--gray-500); display:block;">AVG PACKAGE</span><strong>${data.avg_package_lpa || 'N/A'} LPA</strong></div>
          <div style="background:var(--gray-50); padding:10px; border-radius:6px;"><span style="font-size:11px; color:var(--gray-500); display:block;">HIGHEST PACKAGE</span><strong>${data.highest_package_lpa || 'N/A'} LPA</strong></div>
          <div style="background:var(--gray-50); padding:10px; border-radius:6px;"><span style="font-size:11px; color:var(--gray-500); display:block;">ESTABLISHED</span><strong>${data.established_year || 'N/A'}</strong></div>
          ${placement.placement_percentage ? `<div style="background:var(--gray-50); padding:10px; border-radius:6px;"><span style="font-size:11px; color:var(--gray-500); display:block;">PLACEMENT %</span><strong>${placement.placement_percentage}%</strong></div>` : ''}
        </div>
        <h4 style="margin:16px 0 8px; font-size:15px;">Available Branches (${(data.branches || []).length})</h4>
        <div style="display:flex; flex-wrap:wrap; gap:6px;">
          ${(data.branches || []).map(b => `<span style="background:#e0e7ff; color:#3730a3; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:500;">${b.branch_name} (${b.total_seats} seats)</span>`).join('')}
        </div>`;

      if (typeof showModal === 'function') showModal(html, 'College Details');

    } catch (e) {
      if (typeof showToast === 'function') showToast('Could not load college details.', 'error');
    }
  };

  // ─── Why Modal ────────────────────────────────────────────────────────────
  window.showWhyModal = (explanation) => {
    const whyModal = document.getElementById('why-modal');
    const whyContent = document.getElementById('why-content');
    if (whyModal && whyContent) {
      whyContent.innerHTML = `
        <p style="line-height:1.7; font-size:15px; color:var(--gray-900);">${explanation}</p>
        <p style="font-size:12px; color:var(--gray-500); margin-top:12px; border-top:1px solid var(--gray-200); padding-top:8px;">
          <em>Note: This prediction is estimated using historical cutoff trends and machine learning models.</em>
        </p>`;
      whyModal.classList.add('open');
    } else if (typeof showModal === 'function') {
      showModal(`<p style="line-height:1.7;">${explanation}</p>`, 'Why Recommended?');
    }
  };

  document.getElementById('why-modal')?.querySelector('.close-modal')?.addEventListener('click', () => {
    document.getElementById('why-modal')?.classList.remove('open');
  });

  // ─── Download Report ──────────────────────────────────────────────────────
  window.downloadReport = () => {
    if (predictionData?.prediction_id) {
      window.open(`/api/export/${predictionData.prediction_id}`, '_blank');
    } else {
      if (typeof showToast === 'function') showToast('No prediction to download. Run a prediction first.', 'warning');
    }
  };

  document.getElementById('download-report')?.addEventListener('click', window.downloadReport);

  // ─── Form Submit Listener ─────────────────────────────────────────────────
  const formEl = document.getElementById('prediction-form');
  if (formEl) {
    formEl.addEventListener('submit', (e) => {
      e.preventDefault();
      window.submitPrediction();
    });
  }

  const submitBtn = document.getElementById('submit-prediction');
  if (submitBtn) {
    submitBtn.addEventListener('click', (e) => {
      e.preventDefault();
      window.submitPrediction();
    });
  }

  // ─── Next/Prev Buttons ────────────────────────────────────────────────────
  document.querySelectorAll('.btn-next').forEach(btn => btn.addEventListener('click', window.nextStep));
  document.querySelectorAll('.btn-prev').forEach(btn => btn.addEventListener('click', window.prevStep));

  // ─── Init ─────────────────────────────────────────────────────────────────
  showStep(1);
});
