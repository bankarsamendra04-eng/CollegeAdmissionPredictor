"""
predict.py — Prediction engine for AI College Admission Predictor.

Uses ML model if available, falls back to rule-based prediction.
Clearly labels prediction mode in all responses.
"""

import os
import pickle
import logging
from ml.preprocess import preprocess_student_input

logger = logging.getLogger(__name__)

# Branch name → branch_code mapping (frontend uses full names)
BRANCH_NAME_TO_CODE = {
    'computer science and engineering': 'CSE',
    'computer science & engineering': 'CSE',
    'cse': 'CSE',
    'information technology': 'IT',
    'it': 'IT',
    'artificial intelligence and machine learning': 'AIML',
    'artificial intelligence & machine learning': 'AIML',
    'ai & ml': 'AIML',
    'aiml': 'AIML',
    'ai and data science': 'AIDS',
    'ai & data science': 'AIDS',
    'artificial intelligence and data science': 'AIDS',
    'aids': 'AIDS',
    'data science': 'DS',
    'ds': 'DS',
    'electronics and telecommunication': 'EXTC',
    'electronics & telecommunication': 'EXTC',
    'electronics and telecomm (extc)': 'EXTC',
    'extc': 'EXTC',
    'electronics engineering': 'ELEX',
    'elex': 'ELEX',
    'electrical engineering': 'EE',
    'ee': 'EE',
    'mechanical engineering': 'MECH',
    'mech': 'MECH',
    'civil engineering': 'CIVIL',
    'civil': 'CIVIL',
}


def _normalize_branch(name):
    """Convert branch display name to branch code."""
    return BRANCH_NAME_TO_CODE.get(name.lower().strip(), name.upper().strip())


class PredictionEngine:
    """
    Main prediction engine.

    If ml/model.pkl exists → uses calibrated ML model.
    Otherwise → uses rule-based prediction (clearly labeled).
    """

    def __init__(self, db_manager, model_path=None):
        self.db = db_manager
        self.rule_based = True
        self.model = None
        self.metadata = {}

        if model_path is None:
            model_path = os.getenv('MODEL_PATH', 'ml/model.pkl')

        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                self.model = data.get('model')
                self.metadata = data.get('metadata', {})
                self.rule_based = False
                logger.info(f"ML model loaded: {self.metadata.get('model_name', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}. Using rule-based fallback.")
        else:
            logger.info("No ML model found. Using rule-based prediction.")

    def has_trained_model(self):
        """Returns True if an ML model is loaded."""
        return self.model is not None

    # ------------------------------------------------------------------
    # Core prediction
    # ------------------------------------------------------------------

    def _ml_predict(self, features):
        """Run ML model prediction. Returns probability 0–100."""
        if self.model:
            probs = self.model.predict_proba(features)
            return float(probs[0][1]) * 100
        return 0.0

    def _rule_based_predict(self, student_rank, closing_rank, trend='STABLE'):
        """
        Rule-based probability estimate based on rank ratio.
        Clearly labeled as 'Rule-based estimate' in responses.
        """
        if closing_rank is None or closing_rank <= 0:
            return 30.0  # Neutral default when no cutoff data

        rank_ratio = closing_rank / max(student_rank, 1)

        if rank_ratio >= 1.3:
            base_prob = 0.90
        elif rank_ratio >= 1.1:
            base_prob = 0.80
        elif rank_ratio >= 1.0:
            base_prob = 0.65
        elif rank_ratio >= 0.90:
            base_prob = 0.45
        elif rank_ratio >= 0.75:
            base_prob = 0.25
        elif rank_ratio >= 0.60:
            base_prob = 0.12
        else:
            base_prob = 0.05

        # Trend adjustment
        if trend == 'IMPROVING':
            # Cutoff getting stricter → slightly harder for same rank
            base_prob *= 0.92
        elif trend == 'DECLINING':
            # Cutoff getting easier → slightly better for same rank
            base_prob *= 1.08

        return min(99.0, base_prob * 100)

    def _classify(self, probability):
        """Classify probability into SAFE / MODERATE / DREAM / UNLIKELY."""
        safe_th = float(self.db.get_config('threshold_safe') or 75)
        mod_th = float(self.db.get_config('threshold_moderate') or 40)
        dream_th = float(self.db.get_config('threshold_dream') or 15)

        if probability >= safe_th:
            return 'SAFE'
        elif probability >= mod_th:
            return 'MODERATE'
        elif probability >= dream_th:
            return 'DREAM'
        return 'UNLIKELY'

    def _generate_explanation(self, student_rank, closing_rank, probability, trend,
                               college_name, branch_name, category):
        """Generate human-readable explanation for the prediction."""
        classification = self._classify(probability)
        gap = closing_rank - student_rank if closing_rank else 0

        if gap > 0:
            rank_phrase = (
                f"Your merit rank ({student_rank:,}) is better than the "
                f"historical closing rank ({closing_rank:,}) by {gap:,} ranks"
            )
        elif gap == 0:
            rank_phrase = (
                f"Your merit rank ({student_rank:,}) exactly matches the "
                f"historical closing rank ({closing_rank:,})"
            )
        else:
            rank_phrase = (
                f"Your merit rank ({student_rank:,}) is {abs(gap):,} ranks beyond "
                f"the historical closing rank ({closing_rank:,})"
            )

        trend_phrase = {
            'IMPROVING': 'The cutoff has been getting more competitive (higher demand).',
            'DECLINING': 'The cutoff has been easing in recent years (an advantage for you).',
            'STABLE': 'The cutoff has been stable over the past years.',
        }.get(trend, '')

        category_phrase = f"This estimate is based on the {category} category cutoff."

        explanation_map = {
            'SAFE': (
                f"✅ Recommended as SAFE. {rank_phrase}, giving you a strong advantage. "
                f"{trend_phrase} {category_phrase}"
            ),
            'MODERATE': (
                f"⚡ Recommended as MODERATE. {rank_phrase}. "
                f"Admission is possible but not guaranteed — cutoff can vary by round. "
                f"{trend_phrase} {category_phrase}"
            ),
            'DREAM': (
                f"🎯 Classified as DREAM. {rank_phrase}. "
                f"This college is ambitious based on historical data. "
                f"You may get admission in later rounds if cutoffs ease. "
                f"{trend_phrase} {category_phrase}"
            ),
            'UNLIKELY': (
                f"⚠️ Classified as UNLIKELY. {rank_phrase}. "
                f"Historical data suggests admission is very competitive for your profile. "
                f"Consider this as an aspirational choice. {category_phrase}"
            ),
        }

        return explanation_map.get(classification, f"{rank_phrase}. {trend_phrase}")

    def _get_cutoff_trend(self, college_id, branch_id, category):
        """Determine if cutoff is IMPROVING, STABLE, or DECLINING."""
        trends = self.db.get_cutoff_trends(college_id, branch_id, category)
        if len(trends) >= 2:
            first_rank = trends[0].get('closing_rank', 0)
            last_rank = trends[-1].get('closing_rank', 0)
            if first_rank > 0 and last_rank > 0:
                # Lower closing rank = more competitive (IMPROVING from college perspective)
                if last_rank < first_rank * 0.92:
                    return 'IMPROVING'   # Getting harder (rank falling = more competitive)
                elif last_rank > first_rank * 1.08:
                    return 'DECLINING'   # Getting easier
        return 'STABLE'

    def _calculate_recommendation_score(self, probability, branch_match_score,
                                         location_match_score, college_quality_score,
                                         cutoff_compat_score=50.0):
        """
        Weighted recommendation score (0–100).
        Weights are configurable via app_config table.
        """
        wp = float(self.db.get_config('weight_probability') or 35) / 100.0
        wb = float(self.db.get_config('weight_branch_match') or 20) / 100.0
        wl = float(self.db.get_config('weight_location') or 10) / 100.0
        wq = float(self.db.get_config('weight_quality') or 10) / 100.0
        wc = float(self.db.get_config('weight_cutoff_compat') or 10) / 100.0
        wcp = float(self.db.get_config('weight_college_pref') or 15) / 100.0

        score = (
            probability * wp
            + branch_match_score * wb
            + location_match_score * wl
            + college_quality_score * wq
            + cutoff_compat_score * wc
            + probability * wcp  # college preference proxy via probability
        )
        return round(min(100.0, score), 2)

    # ------------------------------------------------------------------
    # Single college prediction
    # ------------------------------------------------------------------

    def predict_for_college(self, student_data, college_id, branch_id, branch_code='CSE'):
        """
        Predict admission probability for one college+branch.

        Returns dict with probability, classification, explanation, trend, etc.
        """
        student_rank = student_data.get('merit_rank', 10000)
        category = str(student_data.get('category', 'OPEN')).upper().strip()

        # Try to get cutoff for student's category, fallback to OPEN
        cutoffs = self.db.get_cutoffs(
            college_id=college_id, branch_id=branch_id,
            category=category, year=2024, round_no=3
        )
        if not cutoffs:
            cutoffs = self.db.get_cutoffs(
                college_id=college_id, branch_id=branch_id,
                category=category, year=2023, round_no=3
            )
        if not cutoffs:
            cutoffs = self.db.get_cutoffs(
                college_id=college_id, branch_id=branch_id, category='OPEN', round_no=3
            )
        if not cutoffs:
            cutoffs = self.db.get_cutoffs(college_id=college_id, branch_id=branch_id)

        closing_rank = cutoffs[0]['closing_rank'] if cutoffs else None
        opening_rank = cutoffs[0]['opening_rank'] if cutoffs else None

        # Trend analysis
        trend = self._get_cutoff_trend(college_id, branch_id, category)

        # Compute probability
        if not self.rule_based:
            cutoff_info = {
                'closing_rank': closing_rank or 10000,
                'college_tier': 2,
                'branch_code': branch_code,
                'trend_score': {'IMPROVING': 1, 'STABLE': 0, 'DECLINING': -1}.get(trend, 0),
                'round_number': 3,
            }
            features = preprocess_student_input(student_data, cutoff_info)
            probability = self._ml_predict(features)
        else:
            probability = self._rule_based_predict(student_rank, closing_rank, trend)

        classification = self._classify(probability)

        # Explanation
        college_name = cutoffs[0].get('college_name', f'College {college_id}') if cutoffs else f'College {college_id}'
        branch_name = cutoffs[0].get('branch_name', branch_code) if cutoffs else branch_code
        explanation = self._generate_explanation(
            student_rank, closing_rank or 0, probability, trend,
            college_name, branch_name, category
        )

        rank_gap = (closing_rank - student_rank) if closing_rank else 0

        return {
            'probability': round(probability, 1),
            'classification': classification,
            'confidence': 80.0 if not self.rule_based else 65.0,
            'rank_gap': rank_gap,
            'closing_rank_prev': closing_rank,
            'opening_rank_prev': opening_rank,
            'trend': trend,
            'explanation': explanation,
            'prediction_mode': 'ML' if not self.rule_based else 'RULE_BASED',
        }

    # ------------------------------------------------------------------
    # Full prediction (all colleges)
    # ------------------------------------------------------------------

    def predict_all(self, student_data, preferences):
        """
        Run predictions for all matching colleges/branches.
        Applies recommendation scoring and returns sorted results.

        Returns full response dict ready for the API.
        """
        type_normalization = {
            'gov': 'government',
            'government': 'government',
            'gov_aided': 'government-aided',
            'government-aided': 'government-aided',
            'autonomous': 'autonomous',
            'private': 'private',
            'any': 'any'
        }

        student_rank = student_data.get('merit_rank', 10000)
        category = str(student_data.get('category', 'OPEN')).upper().strip()
        gender = str(student_data.get('gender', 'OTHER')).upper().strip()

        preferred_branches_raw = preferences.get('preferred_branches') or []
        preferred_branch_codes = [_normalize_branch(b) for b in preferred_branches_raw if b]
        
        college_type_pref = preferences.get('college_type') or 'Any'
        normalized_type_pref = type_normalization.get(str(college_type_pref).lower().strip(), str(college_type_pref).lower().strip())
        
        preferred_cities = preferences.get('preferred_city') or []
        if isinstance(preferred_cities, str):
            preferred_cities = [preferred_cities] if preferred_cities else []
        preferred_cities_clean = [c.lower().strip() for c in preferred_cities if c]
        no_location_pref = not preferred_cities_clean

        # Get all branches with college info
        all_branches = self.db.get_branches()
        all_colleges_raw = self.db.get_colleges(limit=500)
        colleges_map = {c['id']: c for c in all_colleges_raw.get('colleges', [])}

        # College quality score: normalize avg_package_lpa to 0–100
        packages = [c['avg_package_lpa'] for c in colleges_map.values() if c.get('avg_package_lpa')]
        max_pkg = max(packages) if packages else 20
        min_pkg = min(packages) if packages else 3

        recommendations = []

        for branch in all_branches:
            college_id = branch['college_id']
            branch_id = branch['id']
            branch_code = branch.get('branch_code', 'CSE')
            branch_name = branch.get('branch_name', branch_code)
            college = colleges_map.get(college_id)
            if not college:
                continue

            # Filter by college type preference
            if normalized_type_pref and normalized_type_pref != 'any':
                c_type = str(college.get('college_type', '')).lower().strip()
                if c_type != normalized_type_pref and type_normalization.get(c_type, c_type) != normalized_type_pref:
                    continue

            # Filter by preferred branch (if any specified)
            if preferred_branch_codes:
                if branch_code not in preferred_branch_codes:
                    continue

            # Filter by location (if preference given)
            if not no_location_pref and preferred_cities_clean:
                college_city = str(college.get('city', '')).lower().strip()
                if college_city not in preferred_cities_clean:
                    continue

            # Run prediction
            try:
                pred = self.predict_for_college(student_data, college_id, branch_id, branch_code)
            except Exception as e:
                logger.warning(f"Prediction failed for college {college_id}: {e}")
                continue

            # Scoring components
            branch_match = 1.0 if (preferred_branch_codes and branch_code in preferred_branch_codes) else 0.5
            branch_match_score = branch_match * 100

            location_match = 1.0 if (not no_location_pref and college.get('city') in preferred_cities) else 0.6
            location_match_score = location_match * 100

            pkg = college.get('avg_package_lpa') or min_pkg
            quality_score = ((pkg - min_pkg) / (max_pkg - min_pkg + 0.001)) * 100

            cutoff_compat = min(100.0, max(0.0, 50.0 + pred['rank_gap'] / max(student_rank, 1) * 50))

            rec_score = self._calculate_recommendation_score(
                pred['probability'], branch_match_score,
                location_match_score, quality_score, cutoff_compat
            )

            recommendations.append({
                'college_id': college_id,
                'college_name': college['name'],
                'college_type': college.get('college_type', ''),
                'city': college.get('city', ''),
                'district': college.get('district', ''),
                'state': college.get('state', ''),
                'branch_id': branch_id,
                'branch': branch_name,
                'branch_code': branch_code,
                'probability': pred['probability'],
                'classification': pred['classification'],
                'recommendation_score': rec_score,
                'closing_rank_prev': pred['closing_rank_prev'],
                'opening_rank_prev': pred['opening_rank_prev'],
                'student_rank': student_rank,
                'rank_gap': pred['rank_gap'],
                'trend': pred['trend'],
                'explanation': pred['explanation'],
                'fees': college.get('fees_per_year'),
                'avg_package': college.get('avg_package_lpa'),
                'highest_package': college.get('highest_package_lpa'),
                'accreditation': college.get('accreditation'),
                'naac_grade': college.get('naac_grade'),
                'branch_match_score': round(branch_match_score, 1),
                'confidence': pred['confidence'],
                'prediction_mode': pred['prediction_mode'],
            })

        # Sort by recommendation_score descending
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)

        limit = int(self.db.get_config('prediction_limit') or 50)
        recommendations = recommendations[:limit]

        # Build summary stats
        counts = {'SAFE': 0, 'MODERATE': 0, 'DREAM': 0, 'UNLIKELY': 0}
        for r in recommendations:
            counts[r['classification']] = counts.get(r['classification'], 0) + 1

        best = recommendations[0] if recommendations else None
        best_college = best['college_name'] if best else 'N/A'
        best_branch = best['branch'] if best else 'N/A'
        best_prob = best['probability'] if best else 0

        # Overall outlook score
        if recommendations:
            avg_prob = sum(r['probability'] for r in recommendations[:10]) / min(10, len(recommendations))
        else:
            avg_prob = 0

        if avg_prob >= 70:
            outlook_label = 'Strong Outlook'
            outlook_desc = 'Your profile has a strong chance at several recommended colleges.'
        elif avg_prob >= 40:
            outlook_label = 'Moderate Outlook'
            outlook_desc = 'Your profile has a reasonable chance at some colleges. Consider widening your search.'
        else:
            outlook_label = 'Competitive'
            outlook_desc = 'The colleges on your list are ambitious. Explore a broader range of colleges.'

        disclaimer = (
            "Disclaimer: These are estimated probabilities based on historical cutoff data "
            "and are NOT guarantees of admission. Actual admission depends on official cutoffs, "
            "seat availability, reservation rules, applicant preferences, admission rounds, "
            "and other official factors. Always verify with the official admission authority."
        )

        return {
            'student_summary': {
                'rank': student_rank,
                'category': category,
                'gender': gender,
                'percentile': student_data.get('percentile'),
            },
            'overall_outlook': {
                'score': round(avg_prob, 1),
                'label': outlook_label,
                'description': outlook_desc,
            },
            'recommendations': recommendations,
            'stats': {
                'safe_count': counts['SAFE'],
                'moderate_count': counts['MODERATE'],
                'dream_count': counts['DREAM'],
                'unlikely_count': counts['UNLIKELY'],
                'total': len(recommendations),
            },
            'best_college': best_college,
            'best_branch': best_branch,
            'best_probability': best_prob,
            'prediction_mode': 'ML' if not self.rule_based else 'RULE_BASED',
            'demo_mode': (self.db.get_config('data_mode') or 'demo') == 'demo',
            'disclaimer': disclaimer,
        }
