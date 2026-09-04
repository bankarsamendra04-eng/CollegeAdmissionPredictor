"""
tests/test_prediction.py — Unit tests for the PredictionEngine.
"""

import pytest
from unittest.mock import MagicMock, patch
from ml.predict import PredictionEngine


@pytest.fixture
def mock_db():
    """Mock DatabaseManager with sensible defaults."""
    db = MagicMock()

    # Config values — return numeric strings as the real DB would
    def mock_get_config(key=None):
        config = {
            'threshold_safe': '75',
            'threshold_moderate': '40',
            'threshold_dream': '15',
            'weight_probability': '35',
            'weight_branch_match': '20',
            'weight_college_pref': '15',
            'weight_cutoff_compat': '10',
            'weight_location': '10',
            'weight_quality': '10',
            'prediction_limit': '50',
            'data_mode': 'demo',
        }
        if key:
            return config.get(key, '0')
        return config

    db.get_config.side_effect = mock_get_config

    # Return cutoffs
    db.get_cutoffs.return_value = [
        {'closing_rank': 5000, 'opening_rank': 4000, 'college_name': 'Test College',
         'branch_name': 'CSE', 'branch_code': 'CSE', 'category': 'OPEN', 'gender': 'ALL'}
    ]
    db.get_cutoff_trends.return_value = [
        {'year': 2022, 'closing_rank': 5100},
        {'year': 2023, 'closing_rank': 5000},
        {'year': 2024, 'closing_rank': 4900},
    ]
    db.get_branches.return_value = [
        {'id': 1, 'college_id': 1, 'branch_name': 'Computer Science and Engineering',
         'branch_code': 'CSE', 'college_name': 'Test College'}
    ]
    db.get_colleges.return_value = {
        'colleges': [
            {'id': 1, 'name': 'Test College', 'city': 'Pune', 'district': 'Pune',
             'state': 'Maharashtra', 'college_type': 'Government',
             'fees_per_year': 35000, 'avg_package_lpa': 8.5, 'highest_package_lpa': 30.0,
             'accreditation': 'AICTE', 'naac_grade': 'A', 'nba_accredited': 'Yes',
             'total_seats': 120, 'established_year': 1954, 'university': 'SPPU'}
        ],
        'total': 1
    }
    db.save_prediction.return_value = 1

    return db


@pytest.fixture
def engine(mock_db):
    """PredictionEngine with mock DB (no ML model file needed)."""
    return PredictionEngine(mock_db, model_path='nonexistent_model.pkl')


# ─── Rule-Based Probability Tests ─────────────────────────────────────────────

def test_rule_based_rank_well_below_cutoff(engine):
    """Student rank 1000, cutoff 5000 → should have high probability (> 70%)."""
    prob = engine._rule_based_predict(student_rank=1000, closing_rank=5000)
    assert prob > 70.0, f"Expected > 70%, got {prob}"


def test_rule_based_rank_far_above_cutoff(engine):
    """Student rank 10000, cutoff 2000 → very low probability (< 25%)."""
    prob = engine._rule_based_predict(student_rank=10000, closing_rank=2000)
    assert prob < 25.0, f"Expected < 25%, got {prob}"


def test_rule_based_rank_at_cutoff(engine):
    """Student rank equals cutoff → moderate probability (40-70%)."""
    prob = engine._rule_based_predict(student_rank=5000, closing_rank=5000)
    assert 40.0 <= prob <= 75.0, f"Expected 40-75%, got {prob}"


# ─── Classification Tests ─────────────────────────────────────────────────────

def test_classification_safe(engine):
    """Probability >= 75 → SAFE."""
    assert engine._classify(80) == 'SAFE'
    assert engine._classify(75) == 'SAFE'
    assert engine._classify(99) == 'SAFE'


def test_classification_moderate(engine):
    """Probability 40–74 → MODERATE."""
    assert engine._classify(55) == 'MODERATE'
    assert engine._classify(40) == 'MODERATE'
    assert engine._classify(74) == 'MODERATE'


def test_classification_dream(engine):
    """Probability 15–39 → DREAM."""
    assert engine._classify(25) == 'DREAM'
    assert engine._classify(15) == 'DREAM'
    assert engine._classify(39) == 'DREAM'


def test_classification_unlikely(engine):
    """Probability < 15 → UNLIKELY."""
    assert engine._classify(10) == 'UNLIKELY'
    assert engine._classify(0) == 'UNLIKELY'
    assert engine._classify(14) == 'UNLIKELY'


# ─── Explanation Tests ─────────────────────────────────────────────────────────

def test_explanation_non_empty(engine):
    """Explanation should be a non-empty string."""
    expl = engine._generate_explanation(
        student_rank=5000,
        closing_rank=6000,
        probability=80.0,
        trend='STABLE',
        college_name='Test College',
        branch_name='CSE',
        category='OPEN'
    )
    assert isinstance(expl, str)
    assert len(expl) > 10


def test_explanation_safe_contains_safe(engine):
    """SAFE explanation should mention high chances."""
    expl = engine._generate_explanation(
        student_rank=3000, closing_rank=6000, probability=85.0,
        trend='STABLE', college_name='Test', branch_name='CSE', category='OPEN'
    )
    assert 'SAFE' in expl or 'High' in expl or 'strong' in expl.lower()


def test_explanation_dream_contains_dream(engine):
    """DREAM explanation should mention being ambitious/competitive."""
    expl = engine._generate_explanation(
        student_rank=8000, closing_rank=3000, probability=20.0,
        trend='STABLE', college_name='Test', branch_name='CSE', category='OPEN'
    )
    assert 'DREAM' in expl or 'ambitious' in expl.lower() or 'competitive' in expl.lower()


# ─── predict_all Tests ────────────────────────────────────────────────────────

def test_predict_all_returns_dict(engine):
    """predict_all should return a dict with recommendations key."""
    student_data = {'merit_rank': 3000, 'category': 'OPEN', 'gender': 'MALE', 'percentile': 90.0}
    preferences = {'preferred_branches': ['CSE'], 'college_type': 'Any', 'preferred_city': []}
    result = engine.predict_all(student_data, preferences)
    assert isinstance(result, dict)
    assert 'recommendations' in result
    assert 'overall_outlook' in result
    assert 'stats' in result


def test_predict_all_sorted_by_score(engine):
    """Recommendations should be sorted by recommendation_score descending."""
    student_data = {'merit_rank': 3000, 'category': 'OPEN', 'gender': 'MALE', 'percentile': 90.0}
    preferences = {'preferred_branches': ['CSE'], 'college_type': 'Any', 'preferred_city': []}
    result = engine.predict_all(student_data, preferences)
    recs = result.get('recommendations', [])
    scores = [r.get('recommendation_score', 0) for r in recs]
    assert scores == sorted(scores, reverse=True)


def test_predict_all_has_required_fields(engine):
    """Each recommendation should have all required fields."""
    student_data = {'merit_rank': 3000, 'category': 'OPEN', 'gender': 'MALE', 'percentile': 90.0}
    preferences = {'preferred_branches': ['CSE'], 'college_type': 'Any', 'preferred_city': []}
    result = engine.predict_all(student_data, preferences)
    recs = result.get('recommendations', [])
    if recs:
        rec = recs[0]
        required_fields = ['college_id', 'college_name', 'branch', 'probability',
                           'classification', 'recommendation_score', 'trend', 'explanation']
        for field in required_fields:
            assert field in rec, f"Missing field: {field}"


# ─── Trend Tests ──────────────────────────────────────────────────────────────

def test_cutoff_trend_improving(mock_db):
    """Closing ranks dropping over years → IMPROVING (getting more competitive)."""
    mock_db.get_cutoff_trends.return_value = [
        {'year': 2022, 'closing_rank': 6000},
        {'year': 2023, 'closing_rank': 5500},
        {'year': 2024, 'closing_rank': 4800},
    ]
    eng = PredictionEngine(mock_db, model_path='nonexistent.pkl')
    trend = eng._get_cutoff_trend(1, 1, 'OPEN')
    assert trend == 'IMPROVING'


def test_cutoff_trend_stable(mock_db):
    """Similar closing ranks → STABLE."""
    mock_db.get_cutoff_trends.return_value = [
        {'year': 2022, 'closing_rank': 5000},
        {'year': 2024, 'closing_rank': 5050},
    ]
    eng = PredictionEngine(mock_db, model_path='nonexistent.pkl')
    trend = eng._get_cutoff_trend(1, 1, 'OPEN')
    assert trend == 'STABLE'
