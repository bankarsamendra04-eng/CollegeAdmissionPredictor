import pandas as pd
import numpy as np

def build_training_data(db_manager):
    # Fetch cutoffs
    cutoffs = pd.DataFrame(db_manager.get_cutoffs())
    
    # We want to create realistic target variable 'admitted' based on some logic since we don't have true labels
    # We'll simulate student applications.
    # To do this correctly from historical data, we typically use the cutoffs to build a dataset.
    
    # For a real predictive model, X would be student features + college/branch features, Y = admitted
    # Here, we will just create synthetic instances from the cutoffs.
    
    records = []
    
    # Fetch college stats to get tier
    colleges_result = db_manager.get_colleges(limit=1000)
    colleges_list = colleges_result.get('colleges', []) if isinstance(colleges_result, dict) else colleges_result
    colleges = pd.DataFrame(colleges_list)
    if not colleges.empty and 'avg_package_lpa' in colleges.columns:
        try:
            colleges['college_tier'] = pd.qcut(colleges['avg_package_lpa'].fillna(5), q=3, labels=[3, 2, 1]).astype(int)
            tier_map = dict(zip(colleges['id'], colleges['college_tier']))
        except Exception:
            tier_map = {}
    else:
        tier_map = {}

    branches = pd.DataFrame(db_manager.get_branches())
    if not branches.empty:
        branch_map = dict(zip(branches['id'], branches['branch_code']))
    else:
        branch_map = {}
        
    branch_demand = {
        'CSE': 1.0, 'IT': 0.95, 'AIML': 0.95, 'AIDS': 0.9, 'DS': 0.9,
        'EXTC': 0.8, 'ELEX': 0.75, 'EE': 0.7, 'MECH': 0.6, 'CIVIL': 0.5
    }

    category_map = {'OPEN':0, 'OBC':1, 'SC':2, 'ST':3, 'EWS':4, 'VJ':5, 'NTA':6, 'NTB':7, 'NTC':8, 'NTD':9, 'SBC':10}

    # Simulate 5000 student applications around the cutoffs
    for _, row in cutoffs.sample(min(5000, len(cutoffs))).iterrows():
        c_id = row['college_id']
        b_id = row['branch_id']
        cat = row['category']
        gen = row['gender']
        round_no = row['round']
        closing = row['closing_rank']
        
        # Student 1: Rank better than closing
        sr1 = max(1, int(closing * np.random.uniform(0.5, 0.95)))
        
        # Student 2: Rank worse than closing
        sr2 = int(closing * np.random.uniform(1.05, 1.5))
        
        for sr, admitted in [(sr1, 1), (sr2, 0)]:
            rank_gap = closing - sr
            rank_ratio = closing / sr
            percentile_score = max(0, 100 - (sr / 1000))
            cat_encoded = category_map.get(cat, 0)
            c_tier = tier_map.get(c_id, 2)
            b_code = branch_map.get(b_id, 'MECH')
            b_demand = branch_demand.get(b_code, 0.7)
            is_fem = 1 if gen == 'FEMALE' else 0
            trend_score = 0 # simplified
            
            records.append({
                'rank_gap': rank_gap,
                'rank_ratio': rank_ratio,
                'percentile_score': percentile_score,
                'category_encoded': cat_encoded,
                'college_tier': c_tier,
                'branch_demand_score': b_demand,
                'trend_score': trend_score,
                'is_female_category': is_fem,
                'round_number': round_no,
                'admitted': admitted
            })
            
    df = pd.DataFrame(records)
    if df.empty:
        # fallback dummy data
        df = pd.DataFrame({
            'rank_gap': [100, -100], 'rank_ratio': [1.1, 0.9], 'percentile_score': [90, 80],
            'category_encoded': [0, 1], 'college_tier': [1, 2], 'branch_demand_score': [1.0, 0.8],
            'trend_score': [0, 0], 'is_female_category': [0, 1], 'round_number': [1, 2], 'admitted': [1, 0]
        })
        
    X = df.drop(columns=['admitted'])
    y = df['admitted']
    return X, y

def get_feature_names():
    return [
        'rank_gap', 'rank_ratio', 'percentile_score', 'category_encoded', 
        'college_tier', 'branch_demand_score', 'trend_score', 'is_female_category', 'round_number'
    ]

def preprocess_student_input(student_data, branch_cutoff_info):
    category_map = {'OPEN':0, 'OBC':1, 'SC':2, 'ST':3, 'EWS':4, 'VJ':5, 'NTA':6, 'NTB':7, 'NTC':8, 'NTD':9, 'SBC':10}
    branch_demand = {
        'CSE': 1.0, 'IT': 0.95, 'AIML': 0.95, 'AIDS': 0.9, 'DS': 0.9,
        'EXTC': 0.8, 'ELEX': 0.75, 'EE': 0.7, 'MECH': 0.6, 'CIVIL': 0.5
    }
    
    closing = branch_cutoff_info.get('closing_rank', 10000)
    sr = student_data.get('merit_rank') or student_data.get('rank') or 10000
    try:
        sr = int(sr)
    except (ValueError, TypeError):
        sr = 10000
    
    rank_gap = closing - sr
    rank_ratio = closing / max(sr, 1)
    percentile_score = student_data.get('percentile')
    if percentile_score is None:
        percentile_score = max(0, 100 - (sr / 1000))
    else:
        try:
            percentile_score = float(percentile_score)
        except (ValueError, TypeError):
            percentile_score = max(0, 100 - (sr / 1000))

    cat_str = str(student_data.get('category', 'OPEN')).upper().strip()
    cat_encoded = category_map.get(cat_str, 0)
    c_tier = branch_cutoff_info.get('college_tier', 2)
    b_demand = branch_demand.get(branch_cutoff_info.get('branch_code', 'MECH'), 0.7)
    trend_score = branch_cutoff_info.get('trend_score', 0)
    is_fem = 1 if str(student_data.get('gender', '')).upper().strip() == 'FEMALE' else 0
    round_no = branch_cutoff_info.get('round_number', 1)
    
    feature_dict = {
        'rank_gap': [rank_gap],
        'rank_ratio': [rank_ratio],
        'percentile_score': [percentile_score],
        'category_encoded': [cat_encoded],
        'college_tier': [c_tier],
        'branch_demand_score': [b_demand],
        'trend_score': [trend_score],
        'is_female_category': [is_fem],
        'round_number': [round_no]
    }
    return pd.DataFrame(feature_dict)

