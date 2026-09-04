import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_cors import CORS
from dotenv import load_dotenv

# Import project modules
from database.database import DatabaseManager
from ml.predict import PredictionEngine

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-secret-key')
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS
    CORS(app)
    
    # Initialize services
    try:
        db = DatabaseManager()
        db.initialize()
        prediction_engine = PredictionEngine(db)
        if not prediction_engine.has_trained_model():
            try:
                from ml.train import train_models
                train_models(db)
                prediction_engine = PredictionEngine(db)
            except Exception as te:
                logger.warning(f"Auto-training on startup skipped: {te}")
        logger.info("Database and PredictionEngine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        # In a real app we might not want to start if critical services fail,
        # but for this structure we'll let it try and fail gracefully on endpoints.
        db = None
        prediction_engine = None

    # Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error=str(e.description)), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Resource not found"), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify(error="Internal server error"), 500

    # Page Routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/predictor')
    def predictor():
        return render_template('predictor.html')

    @app.route('/colleges')
    def colleges():
        return render_template('colleges.html')

    @app.route('/analytics')
    def analytics():
        return render_template('analytics.html')

    @app.route('/compare')
    def compare():
        return render_template('colleges.html', compare_mode=True)

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/disclaimer')
    def disclaimer():
        return render_template('disclaimer.html')

    # API Routes
    @app.route('/api/stats', methods=['GET'])
    def api_stats():
        try:
            stats = db.get_stats() if db else {}
            colleges_count = stats.get('colleges_count', 0)
            branches_count = stats.get('branches_count', 0)
            historical_records = stats.get('historical_records', 0)
            has_model = prediction_engine and prediction_engine.has_trained_model()
            if has_model and prediction_engine.metadata.get('metrics'):
                auc = prediction_engine.metadata['metrics'].get('auc', 0)
                prediction_accuracy_note = f"Model AUC: {auc:.3f} (run ml/train.py to retrain)"
            elif has_model:
                prediction_accuracy_note = "ML model loaded (run ml/train.py to see metrics)"
            else:
                prediction_accuracy_note = "Model evaluation available after training"
            
            return jsonify({
                'colleges_count': colleges_count,
                'branches_count': branches_count,
                'historical_records': historical_records,
                'prediction_accuracy_note': prediction_accuracy_note
            })
        except Exception as e:
            logger.error(f"Error in /api/stats: {e}")
            return jsonify(error="Failed to fetch stats"), 500

    @app.route('/api/colleges', methods=['GET'])
    def api_colleges():
        try:
            college_types = request.args.getlist('college_type')
            if not college_types and request.args.get('college_type'):
                college_types = [request.args.get('college_type')]

            filters = {
                'search': request.args.get('search', '').strip(),
                'college_type': college_types,
                'city': request.args.get('city', '').strip(),
                'district': request.args.get('district', '').strip(),
                'state': request.args.get('state', '').strip(),
                'min_fees': request.args.get('min_fees', type=int),
                'max_fees': request.args.get('max_fees', type=int),
                'sort': request.args.get('sort', 'name').strip(),
            }
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 12, type=int)
            
            result = db.get_colleges(filters, page, limit) if db else {'colleges': [], 'total': 0}
            
            return jsonify({
                'colleges': result.get('colleges', []),
                'total': result.get('total', 0),
                'page': page,
                'limit': limit
            })
        except Exception as e:
            logger.error(f"Error in /api/colleges: {e}")
            return jsonify(error="Failed to fetch colleges"), 500

    @app.route('/api/college/<int:id>', methods=['GET'])
    def api_college_details(id):
        try:
            college = db.get_college_by_id(id) if db else None
            if not college:
                abort(404, description="College not found")
            return jsonify(college)
        except Exception as e:
            logger.error(f"Error in /api/college/{id}: {e}")
            abort(404, description="College not found")

    @app.route('/api/branches', methods=['GET'])
    def api_branches():
        try:
            college_id = request.args.get('college_id', type=int)
            branches = db.get_branches(college_id) if db else []
            return jsonify({'branches': branches})
        except Exception as e:
            logger.error(f"Error in /api/branches: {e}")
            return jsonify(error="Failed to fetch branches"), 500

    @app.route('/api/categories', methods=['GET'])
    def api_categories():
        return jsonify({
            'categories': [
                {'code': 'OPEN', 'name': 'Open Category', 'description': 'General Category'},
                {'code': 'OBC', 'name': 'Other Backward Class', 'description': 'OBC Category'},
                {'code': 'SC', 'name': 'Scheduled Caste', 'description': 'SC Category'},
                {'code': 'ST', 'name': 'Scheduled Tribe', 'description': 'ST Category'},
                {'code': 'EWS', 'name': 'Economically Weaker Section', 'description': 'EWS Category'},
                {'code': 'VJ', 'name': 'Vimukta Jati', 'description': 'VJ Category'},
                {'code': 'NTA', 'name': 'Nomadic Tribe A', 'description': 'NT-A Category'},
                {'code': 'NTB', 'name': 'Nomadic Tribe B', 'description': 'NT-B Category'},
                {'code': 'NTC', 'name': 'Nomadic Tribe C', 'description': 'NT-C Category'},
                {'code': 'NTD', 'name': 'Nomadic Tribe D', 'description': 'NT-D Category'},
                {'code': 'SBC', 'name': 'Special Backward Class', 'description': 'SBC Category'}
            ],
            'genders': [
                {'code': 'ALL', 'name': 'All / Both'},
                {'code': 'FEMALE', 'name': 'Female Only'}
            ]
        })

    @app.route('/api/cutoffs', methods=['GET'])
    def api_cutoffs():
        try:
            filters = {
                'college_id': request.args.get('college_id', type=int),
                'branch_id': request.args.get('branch_id', type=int),
                'category': request.args.get('category'),
                'year': request.args.get('year', type=int),
                'round': request.args.get('round', type=int),
                'gender': request.args.get('gender')
            }
            cutoffs = db.get_cutoffs(filters) if db else []
            return jsonify({'cutoffs': cutoffs})
        except Exception as e:
            logger.error(f"Error in /api/cutoffs: {e}")
            return jsonify(error="Failed to fetch cutoffs"), 500

    @app.route('/api/analytics', methods=['GET'])
    def api_analytics():
        try:
            filters = {
                'category': request.args.get('category', 'OPEN'),
                'college': request.args.get('college'),
                'branch': request.args.get('branch'),
                'years': request.args.get('years')
            }
            analytics_data = db.get_analytics(filters) if db else {
                'cutoff_trends': [],
                'top_colleges': [],
                'branch_demand': [],
                'category_distribution': []
            }
            return jsonify(analytics_data)
        except Exception as e:
            logger.error(f"Error in /api/analytics: {e}")
            return jsonify(error="Failed to fetch analytics"), 500

    @app.route('/api/config', methods=['GET'])
    def api_config():
        try:
            config_data = db.get_config() if db else {}
            return jsonify(config_data)
        except Exception as e:
            logger.error(f"Error in /api/config: {e}")
            return jsonify(error="Failed to fetch config"), 500

    @app.route('/api/predict', methods=['POST'])
    def api_predict():
        try:
            data = request.json
            if not data:
                abort(400, description="Invalid request payload")

            # Validation
            merit_rank = data.get('merit_rank')
            if merit_rank is None or not isinstance(merit_rank, (int, float)) or int(merit_rank) <= 0:
                abort(400, description="merit_rank is required and must be a positive integer")
            merit_rank = int(merit_rank)
                
            category = data.get('category')
            if not category:
                abort(400, description="category is required")
            category = str(category).upper().strip()
                
            percentile = data.get('percentile')
            if percentile is not None and str(percentile).strip() != '':
                try:
                    percentile = float(percentile)
                    if percentile < 0 or percentile > 100:
                        abort(400, description="percentile must be between 0 and 100")
                except ValueError:
                    abort(400, description="percentile must be a valid number between 0 and 100")
            else:
                percentile = None
                
            preferred_branches = data.get('preferred_branches', [])
            if not preferred_branches or not isinstance(preferred_branches, list):
                abort(400, description="At least one preferred branch should be provided")

            # Process prediction
            if not prediction_engine:
                abort(500, description="Prediction engine not initialized")
                
            student_data = {
                'merit_rank': merit_rank,
                'category_rank': data.get('category_rank'),
                'percentile': percentile,
                'entrance_score': data.get('entrance_score'),
                'category': category,
                'gender': str(data.get('gender', 'OTHER')).upper().strip(),
                'diploma_percentage': data.get('diploma_percentage'),
                'twelfth_percentage': data.get('twelfth_percentage'),
                'cgpa': data.get('cgpa')
            }
            
            preferences = {
                'preferred_branches': preferred_branches,
                'college_type': data.get('college_type', 'Any'),
                'preferred_state': data.get('preferred_state'),
                'preferred_city': data.get('preferred_city'),
                'entrance_exam': data.get('entrance_exam')
            }
            
            results = prediction_engine.predict_all(student_data, preferences)
            
            # Save prediction to DB
            prediction_id = db.save_prediction(student_data, preferences, results) if db else "tmp_123"
            prediction_id = str(prediction_id)
            
            results['prediction_id'] = prediction_id
            return jsonify(results)
            
        except Exception as e:
            logger.error(f"Error in /api/predict: {e}")
            if "400" in str(e):
                abort(400, description=str(e))
            return jsonify(error="Prediction failed"), 500

    @app.route('/api/compare', methods=['POST'])
    def api_compare():
        try:
            data = request.json or {}
            college_ids_raw = data.get('college_ids', [])
            if not isinstance(college_ids_raw, list):
                abort(400, description="college_ids must be a list")
                
            college_ids = [int(cid) for cid in college_ids_raw if str(cid).isdigit()]
            branch_ids_raw = data.get('branch_ids', [])
            branch_ids = [int(bid) if str(bid).isdigit() else None for bid in branch_ids_raw] if isinstance(branch_ids_raw, list) else None
            category = str(data.get('category', 'OPEN')).upper().strip()
                
            comparison_data = db.get_comparison(college_ids[:4], branch_ids, category) if db else []
            return jsonify({'colleges': comparison_data})
            
        except Exception as e:
            logger.error(f"Error in /api/compare: {e}")
            return jsonify(error="Comparison failed"), 500

    @app.route('/api/export/<prediction_id>', methods=['GET'])
    def api_export(prediction_id):
        try:
            prediction = db.get_prediction_by_id(int(prediction_id)) if db else None

            result_data = {}
            student_data = {}
            if prediction:
                result_data = prediction.get('result', {})
                student_data = prediction.get('input_data', {})

            # Extract data
            rank_val = student_data.get('merit_rank')
            rank_str = f"{rank_val:,}" if isinstance(rank_val, (int, float)) else str(rank_val or 'N/A')
            cat_str = str(student_data.get('category', 'N/A'))
            perc_str = str(student_data.get('percentile', 'N/A'))
            gender_str = str(student_data.get('gender', 'N/A'))
            score_str = str(student_data.get('entrance_score', 'N/A'))

            overall_outlook = result_data.get('overall_outlook') or {}
            outlook_score = overall_outlook.get('score', 0)
            outlook_label = overall_outlook.get('label', 'N/A')
            outlook_desc = overall_outlook.get('description', '')

            stats = result_data.get('stats') or {}
            safe_count = stats.get('safe_count', 0)
            moderate_count = stats.get('moderate_count', 0)
            dream_count = stats.get('dream_count', 0)

            # Build HTML report
            recommendations = result_data.get('recommendations', [])[:20]
            recs_html = ""
            for r in recommendations:
                cls_color = {'SAFE': '#16a34a', 'MODERATE': '#d97706', 'DREAM': '#dc2626', 'UNLIKELY': '#6b7280'}.get(r.get('classification', ''), '#6b7280')
                fees_str = f"₹{(r.get('fees') or 0):,}/yr"
                recs_html += f"""
                <tr>
                    <td>{r.get('college_name', '')}</td>
                    <td>{r.get('branch', '')}</td>
                    <td>{r.get('city', '')}</td>
                    <td><strong style="color:{cls_color}">{r.get('classification', '')}</strong></td>
                    <td>{r.get('probability', 0):.1f}%</td>
                    <td>{r.get('closing_rank_prev', 'N/A')}</td>
                    <td>{fees_str}</td>
                    <td>{r.get('avg_package', 'N/A')} LPA</td>
                </tr>"""

            report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admission Prediction Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #1e293b; }}
        .header {{ text-align: center; border-bottom: 3px solid #2563eb; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ color: #2563eb; font-size: 28px; margin: 0; }}
        .header p {{ color: #64748b; margin: 8px 0 0; }}
        .demo-banner {{ background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 10px 16px; margin-bottom: 24px; font-size: 14px; color: #92400e; text-align: center; }}
        .section {{ margin-bottom: 28px; }}
        .section h2 {{ font-size: 18px; color: #1e40af; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 16px; }}
        .profile-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }}
        .profile-item {{ background: #f8fafc; border-radius: 8px; padding: 12px; }}
        .profile-item .label {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }}
        .profile-item .value {{ font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 4px; }}
        .outlook {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 20px; }}
        .outlook .score {{ font-size: 48px; font-weight: 800; }}
        .outlook .label {{ font-size: 20px; font-weight: 600; margin: 8px 0 4px; }}
        .outlook .desc {{ opacity: 0.9; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background: #1e40af; color: white; padding: 10px 12px; text-align: left; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; }}
        tr:nth-child(even) {{ background: #f8fafc; }}
        .disclaimer {{ background: #fef2f2; border: 1px solid #fca5a5; border-radius: 8px; padding: 16px; font-size: 13px; color: #7f1d1d; margin-top: 30px; }}
        .footer-note {{ text-align: center; font-size: 12px; color: #94a3b8; margin-top: 24px; }}
        @media print {{ body {{ margin: 20px; }} .no-print {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎓 AI College Admission Predictor</h1>
        <p>Personalized Admission Prediction Report</p>
        <p style="font-size:12px;color:#94a3b8;">Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>

    <div class="demo-banner">
        ⚠️ DEMO DATA — This report uses sample/demonstration data. Predictions are illustrative only.
    </div>

    <div class="section">
        <h2>Student Profile</h2>
        <div class="profile-grid">
            <div class="profile-item">
                <div class="label">Merit Rank</div>
                <div class="value">{rank_str}</div>
            </div>
            <div class="profile-item">
                <div class="label">Category</div>
                <div class="value">{cat_str}</div>
            </div>
            <div class="profile-item">
                <div class="label">Percentile</div>
                <div class="value">{perc_str}</div>
            </div>
            <div class="profile-item">
                <div class="label">Gender</div>
                <div class="value">{gender_str}</div>
            </div>
            <div class="profile-item">
                <div class="label">Entrance Score</div>
                <div class="value">{score_str}</div>
            </div>
            <div class="profile-item">
                <div class="label">Prediction ID</div>
                <div class="value" style="font-size:13px;">#{prediction_id}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Overall Admission Outlook</h2>
        <div class="outlook">
            <div class="score">{outlook_score:.0f}%</div>
            <div class="label">{outlook_label}</div>
            <div class="desc">{outlook_desc}</div>
        </div>
        <div class="profile-grid">
            <div class="profile-item">
                <div class="label">✅ Safe Colleges</div>
                <div class="value" style="color:#16a34a">{safe_count}</div>
            </div>
            <div class="profile-item">
                <div class="label">⚡ Moderate</div>
                <div class="value" style="color:#d97706">{moderate_count}</div>
            </div>
            <div class="profile-item">
                <div class="label">🎯 Dream</div>
                <div class="value" style="color:#dc2626">{dream_count}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>College Recommendations</h2>
        <table>
            <thead>
                <tr>
                    <th>College</th><th>Branch</th><th>City</th>
                    <th>Status</th><th>Probability</th><th>Closing Rank</th>
                    <th>Fees/yr</th><th>Avg Package</th>
                </tr>
            </thead>
            <tbody>
                {recs_html}
            </tbody>
        </table>
    </div>

    <div class="disclaimer">
        <strong>⚠️ Important Disclaimer:</strong> This tool provides estimated admission probabilities
        based on available historical data and user-provided information. It does NOT guarantee admission.
        Actual admission depends on official cutoffs, seat availability, reservation rules, applicant
        preferences, admission rounds, and other factors. Always verify final information with the
        official admission authority and college.
    </div>

    <div class="footer-note">
        AI College Admission Predictor — Demo Mode | Data is for demonstration purposes only
    </div>

    <script>window.onload = function() {{ window.print(); }}</script>
</body>
</html>"""

            return report_html, 200, {
                'Content-Type': 'text/html; charset=utf-8',
                'Content-Disposition': f'inline; filename="admission_report_{prediction_id}.html"'
            }

        except Exception as e:
            logger.error(f"Error in /api/export/{prediction_id}: {e}")
            return jsonify(error="Export failed"), 500

    return app

app = create_app()

if __name__ == '__main__':
    # Initialize DB (create tables + load CSV if empty)
    try:
        db = DatabaseManager()
        db.initialize()
    except Exception as e:
        print(f"Startup DB init failed: {e}")
        
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, port=5000)
