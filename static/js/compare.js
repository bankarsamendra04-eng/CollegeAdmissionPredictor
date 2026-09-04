// COMPARE MODULE (shared between predictor and colleges pages)

const CompareModule = {
  list: [],        // [{college_id, branch_id, name, branch}]
  maxItems: 4,
  
  add(college) {
    if (this.list.length >= this.maxItems) {
      showToast(\`You can only compare up to \${this.maxItems} colleges at once.\`, 'warning');
      return;
    }
    
    const exists = this.list.find(c => c.college_id === college.college_id && c.branch_id === college.branch_id);
    if (exists) {
      showToast('Already added to compare list', 'info');
      return;
    }
    
    this.list.push(college);
    this.updateBar();
    showToast(\`Added \${college.name} to compare list\`, 'success');
  },
  
  remove(collegeId) {
    this.list = this.list.filter(c => c.college_id !== collegeId);
    this.updateBar();
  },
  
  clear() {
    this.list = [];
    this.updateBar();
  },
  
  renderPanel() {
    // Optional: Render a side panel or just update the bottom bar
  },
  
  updateBar() {
    let bar = document.getElementById('compare-bar');
    if (!bar) {
      bar = document.createElement('div');
      bar.id = 'compare-bar';
      bar.style.cssText = 'position: fixed; bottom: 0; left: 0; width: 100%; background: #343a40; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; z-index: 1000; transform: translateY(100%); transition: transform 0.3s;';
      
      const info = document.createElement('div');
      info.id = 'compare-bar-info';
      
      const actions = document.createElement('div');
      
      const compareBtn = document.createElement('button');
      compareBtn.innerText = 'Compare Now';
      compareBtn.className = 'btn btn-primary mr-2';
      compareBtn.onclick = () => this.openModal();
      
      const clearBtn = document.createElement('button');
      clearBtn.innerText = 'Clear';
      clearBtn.className = 'btn btn-secondary';
      clearBtn.onclick = () => this.clear();
      
      actions.appendChild(compareBtn);
      actions.appendChild(clearBtn);
      
      bar.appendChild(info);
      bar.appendChild(actions);
      document.body.appendChild(bar);
    }
    
    if (this.list.length > 0) {
      document.getElementById('compare-bar-info').innerText = \`\${this.list.length} College(s) selected for comparison\`;
      bar.style.transform = 'translateY(0)';
    } else {
      bar.style.transform = 'translateY(100%)';
    }
  },
  
  async openModal() {
    if (this.list.length < 2) {
      showToast('Select at least 2 colleges to compare', 'warning');
      return;
    }
    
    try {
      const payload = {
        college_ids: this.list.map(c => c.college_id),
        branch_ids: this.list.map(c => c.branch_id),
        category: document.getElementById('category-filter') ? document.getElementById('category-filter').value : 'OPEN'
      };
      
      const data = await apiFetch('/api/compare', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      if (data && data.colleges) {
        this.renderTable(data);
      }
    } catch (error) {
      console.error(error);
    }
  },
  
  renderTable(data) {
    const colleges = data.colleges;
    let html = '<div class="table-responsive"><table class="table table-bordered table-striped text-center"><thead><tr><th>Feature</th>';
    
    colleges.forEach(c => {
      html += \`<th>\${c.name}<br><small>\${c.branch || ''}</small></th>\`;
    });
    html += '</tr></thead><tbody>';
    
    const rows = [
      { key: 'probability', label: 'Admission Probability', higherIsBetter: true, format: (v) => v ? \`\${v}%\` : 'N/A' },
      { key: 'closing_rank', label: 'Previous Closing Rank', higherIsBetter: false, format: (v) => v || 'N/A' },
      { key: 'fees', label: 'Annual Fees', higherIsBetter: false, format: formatCurrency },
      { key: 'avg_package', label: 'Avg Package (LPA)', higherIsBetter: true, format: formatPackage },
      { key: 'highest_package', label: 'Highest Package (LPA)', higherIsBetter: true, format: formatPackage },
      { key: 'placement_pct', label: 'Placement %', higherIsBetter: true, format: (v) => v ? \`\${v}%\` : 'N/A' },
      { key: 'city', label: 'Location', higherIsBetter: null, format: (v) => v || 'N/A' },
      { key: 'college_type', label: 'College Type', higherIsBetter: null, format: (v) => v || 'N/A' },
      { key: 'naac_grade', label: 'NAAC Grade', higherIsBetter: null, format: (v) => v || 'N/A' }
    ];
    
    rows.forEach(row => {
      html += \`<tr><td><strong>\${row.label}</strong></td>\`;
      
      const values = colleges.map(c => c[row.key]);
      const highlights = this.highlightBetter(values, row.higherIsBetter);
      
      colleges.forEach((c, idx) => {
        let cellClass = '';
        if (highlights[idx] === 'best') cellClass = 'bg-success text-white font-weight-bold';
        else if (highlights[idx] === 'worst') cellClass = 'bg-danger text-white';
        
        html += \`<td class="\${cellClass}">\${row.format(c[row.key])}</td>\`;
      });
      
      html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    
    showModal(html, 'College Comparison');
  },
  
  highlightBetter(values, higherIsBetter) {
    const result = new Array(values.length).fill('');
    if (higherIsBetter === null) return result;
    
    let validValues = values.map(v => parseFloat(v)).filter(v => !isNaN(v));
    if (validValues.length === 0) return result;
    
    const max = Math.max(...validValues);
    const min = Math.min(...validValues);
    
    values.forEach((v, idx) => {
      const num = parseFloat(v);
      if (isNaN(num)) return;
      
      if (higherIsBetter) {
        if (num === max) result[idx] = 'best';
        else if (num === min) result[idx] = 'worst';
      } else {
        if (num === min) result[idx] = 'best';
        else if (num === max) result[idx] = 'worst';
      }
    });
    
    return result;
  }
};

window.CompareModule = CompareModule;
