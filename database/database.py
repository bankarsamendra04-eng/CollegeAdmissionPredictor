"""
database.py — SQLite database manager for AI College Admission Predictor
DEMO DATA mode: loads data from CSV files in data/ directory.
"""

import sqlite3
import pandas as pd
import os
import json
import contextlib
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations using SQLite."""

    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', 'admission_predictor.db')
        self.db_path = db_path

    @contextlib.contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def create_tables(self):
        """Create all tables and indexes if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS colleges (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT,
                district TEXT,
                state TEXT,
                college_type TEXT,
                university TEXT,
                fees_per_year INTEGER,
                avg_package_lpa REAL,
                highest_package_lpa REAL,
                accreditation TEXT,
                established_year INTEGER,
                naac_grade TEXT,
                nba_accredited TEXT,
                total_seats INTEGER
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS branches (
                id INTEGER PRIMARY KEY,
                college_id INTEGER,
                branch_name TEXT,
                branch_code TEXT,
                total_seats INTEGER,
                open_seats INTEGER,
                obc_seats INTEGER,
                sc_seats INTEGER,
                st_seats INTEGER,
                ews_seats INTEGER,
                vjdt_seats INTEGER,
                nt_seats INTEGER,
                sbc_seats INTEGER,
                FOREIGN KEY (college_id) REFERENCES colleges(id)
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cutoffs (
                id INTEGER PRIMARY KEY,
                college_id INTEGER,
                branch_id INTEGER,
                year INTEGER,
                category TEXT,
                gender TEXT,
                round INTEGER,
                opening_rank INTEGER,
                closing_rank INTEGER,
                FOREIGN KEY (college_id) REFERENCES colleges(id),
                FOREIGN KEY (branch_id) REFERENCES branches(id)
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS placements (
                id INTEGER PRIMARY KEY,
                college_id INTEGER,
                year INTEGER,
                companies_visited INTEGER,
                students_placed INTEGER,
                placement_percentage REAL,
                avg_package_lpa REAL,
                median_package_lpa REAL,
                highest_package_lpa REAL,
                FOREIGN KEY (college_id) REFERENCES colleges(id)
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_rank INTEGER,
                category TEXT,
                gender TEXT,
                preferred_branches TEXT,
                preferred_cities TEXT,
                input_data TEXT,
                result TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            ''')

            # Indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cutoffs_lookup ON cutoffs(college_id, branch_id, year, category, gender, round)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_branches_college ON branches(college_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_placements_college ON placements(college_id)')

            conn.commit()
            logger.info("Database tables created/verified.")

    def seed_config(self):
        """Insert default configuration values (idempotent)."""
        defaults = {
            'threshold_safe': '75',
            'threshold_moderate': '40',
            'threshold_dream': '15',
            'weight_probability': '35',
            'weight_branch_match': '20',
            'weight_college_pref': '15',
            'weight_cutoff_compat': '10',
            'weight_location': '10',
            'weight_quality': '10',
            'data_mode': os.getenv('DATA_MODE', 'demo'),
            'prediction_limit': '50',
        }
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for k, v in defaults.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO app_config (key, value) VALUES (?, ?)",
                    (k, v)
                )
            conn.commit()

    def load_from_csv(self, data_dir='data'):
        """Load CSV data into SQLite. Replaces existing data."""
        with self.get_connection() as conn:
            for table in ['colleges', 'branches', 'cutoffs', 'placements']:
                csv_path = os.path.join(data_dir, f"{table}.csv")
                if not os.path.exists(csv_path):
                    logger.warning(f"CSV not found: {csv_path}")
                    continue
                try:
                    df = pd.read_csv(csv_path, comment='#')
                    df.to_sql(table, conn, if_exists='replace', index=False)
                    logger.info(f"Loaded {len(df)} rows into '{table}'.")
                except Exception as e:
                    logger.error(f"Failed to load {table}.csv: {e}")
            conn.commit()

    def initialize(self, data_dir='data'):
        """Full initialization: create tables, seed config, load CSV if empty."""
        self.create_tables()
        self.seed_config()

        # Only load CSV if colleges table is empty
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as c FROM colleges")
            count = cursor.fetchone()['c']

        if count == 0:
            logger.info("Database is empty. Loading from CSV files...")
            self.load_from_csv(data_dir)
        else:
            logger.info(f"Database already has {count} colleges. Skipping CSV load.")

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def get_config(self, key=None):
        """Get one config value by key, or all config as dict."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if key:
                cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
                row = cursor.fetchone()
                return row['value'] if row else None
            else:
                cursor.execute("SELECT key, value FROM app_config")
                return {row['key']: row['value'] for row in cursor.fetchall()}

    def set_config(self, key, value):
        """Set a config value."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)",
                (key, str(value))
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Colleges
    # ------------------------------------------------------------------

    def get_colleges(self, filters=None, page=1, limit=20):
        """Get colleges with optional filtering, pagination. Returns dict with colleges list and total."""
        type_mapping = {
            'gov': 'Government',
            'government': 'Government',
            'gov_aided': 'Government-Aided',
            'government-aided': 'Government-Aided',
            'autonomous': 'Autonomous',
            'private': 'Private',
            'university department': 'University Department'
        }

        with self.get_connection() as conn:
            cursor = conn.cursor()
            where_clauses = ["1=1"]
            params = []

            if filters:
                search = filters.get('search', '')
                if search:
                    where_clauses.append("(name LIKE ? OR city LIKE ? OR district LIKE ? OR university LIKE ?)")
                    params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])

                college_type = filters.get('college_type', '')
                if college_type:
                    if isinstance(college_type, str):
                        # Could be comma-separated or single
                        types = [t.strip() for t in college_type.split(',') if t.strip() and t.lower() != 'any']
                    elif isinstance(college_type, (list, tuple, set)):
                        types = [t.strip() for t in college_type if t and str(t).lower() != 'any']
                    else:
                        types = []

                    if types:
                        mapped_types = [type_mapping.get(t.lower(), t) for t in types]
                        placeholders = ','.join(['?'] * len(mapped_types))
                        where_clauses.append(f"college_type IN ({placeholders})")
                        params.extend(mapped_types)

                city = filters.get('city', '')
                if city:
                    where_clauses.append("LOWER(city) = LOWER(?)")
                    params.append(city)

                district = filters.get('district', '')
                if district:
                    where_clauses.append("LOWER(district) = LOWER(?)")
                    params.append(district)

                state = filters.get('state', '')
                if state:
                    where_clauses.append("LOWER(state) = LOWER(?)")
                    params.append(state)

                min_fees = filters.get('min_fees')
                if min_fees is not None and str(min_fees).strip() != '':
                    try:
                        where_clauses.append("fees_per_year >= ?")
                        params.append(int(min_fees))
                    except (ValueError, TypeError):
                        pass

                max_fees = filters.get('max_fees')
                if max_fees is not None and str(max_fees).strip() != '':
                    try:
                        where_clauses.append("fees_per_year <= ?")
                        params.append(int(max_fees))
                    except (ValueError, TypeError):
                        pass

                naac = filters.get('naac_grade')
                if naac:
                    if isinstance(naac, list):
                        placeholders = ','.join(['?'] * len(naac))
                        where_clauses.append(f"naac_grade IN ({placeholders})")
                        params.extend(naac)
                    else:
                        where_clauses.append("naac_grade = ?")
                        params.append(naac)

            sort = (filters or {}).get('sort', 'name')
            sort_map = {
                'name': 'name ASC',
                'ranking': 'avg_package_lpa DESC, fees_per_year ASC',
                'relevance': 'id ASC',
                'fees_asc': 'fees_per_year ASC',
                'fees-low': 'fees_per_year ASC',
                'fees_desc': 'fees_per_year DESC',
                'fees-high': 'fees_per_year DESC',
                'package_desc': 'avg_package_lpa DESC',
                'package': 'avg_package_lpa DESC',
                'established': 'established_year ASC',
            }
            order_by = sort_map.get(sort, 'name ASC')

            where_sql = " AND ".join(where_clauses)

            # Count total
            cursor.execute(f"SELECT COUNT(*) as c FROM colleges WHERE {where_sql}", params)
            total = cursor.fetchone()['c']

            # Paginated query
            offset = max(0, (page - 1) * limit)
            cursor.execute(
                f"SELECT * FROM colleges WHERE {where_sql} ORDER BY {order_by} LIMIT ? OFFSET ?",
                params + [limit, offset]
            )
            colleges = [dict(row) for row in cursor.fetchall()]

            return {'colleges': colleges, 'total': total}

    def get_college_by_id(self, college_id):
        """Get full college details including branches, cutoffs, and placements."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM colleges WHERE id = ?", (college_id,))
            row = cursor.fetchone()
            if not row:
                return None

            college = dict(row)

            # Branches with their latest cutoffs
            cursor.execute("SELECT * FROM branches WHERE college_id = ?", (college_id,))
            branches = []
            for b in cursor.fetchall():
                branch = dict(b)
                # Get cutoffs for this branch (last 3 years)
                cursor.execute('''
                    SELECT year, category, gender, round, opening_rank, closing_rank
                    FROM cutoffs
                    WHERE college_id = ? AND branch_id = ?
                    ORDER BY year DESC, round DESC
                ''', (college_id, b['id']))
                branch['cutoffs'] = [dict(c) for c in cursor.fetchall()]
                branches.append(branch)
            college['branches'] = branches

            # Placement stats
            cursor.execute(
                "SELECT * FROM placements WHERE college_id = ? ORDER BY year DESC",
                (college_id,)
            )
            college['placements'] = [dict(p) for p in cursor.fetchall()]

            return college

    # ------------------------------------------------------------------
    # Branches
    # ------------------------------------------------------------------

    def get_branches(self, college_id=None, limit=1000):
        """Get branches, optionally filtered by college."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if college_id:
                cursor.execute(
                    "SELECT b.*, c.name as college_name FROM branches b JOIN colleges c ON b.college_id = c.id WHERE b.college_id = ?",
                    (college_id,)
                )
            else:
                cursor.execute(
                    "SELECT b.*, c.name as college_name FROM branches b JOIN colleges c ON b.college_id = c.id LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Cutoffs
    # ------------------------------------------------------------------

    def get_cutoffs(self, filters=None, college_id=None, branch_id=None,
                    year=None, category=None, round_no=None, gender=None):
        """Get cutoffs with flexible filtering."""
        with self.get_connection() as conn:
            query = '''
                SELECT c.*, col.name as college_name, b.branch_name, b.branch_code
                FROM cutoffs c
                JOIN colleges col ON c.college_id = col.id
                JOIN branches b ON c.branch_id = b.id
                WHERE 1=1
            '''
            params = []

            # Support both dict filters and keyword args
            if filters:
                college_id = filters.get('college_id') or college_id
                branch_id = filters.get('branch_id') or branch_id
                year = filters.get('year') or year
                category = filters.get('category') or category
                round_no = filters.get('round') or round_no
                gender = filters.get('gender') or gender

            if college_id:
                query += " AND c.college_id = ?"
                params.append(college_id)
            if branch_id:
                query += " AND c.branch_id = ?"
                params.append(branch_id)
            if year:
                query += " AND c.year = ?"
                params.append(year)
            if category:
                query += " AND c.category = ?"
                params.append(category)
            if round_no:
                query += " AND c.round = ?"
                params.append(round_no)
            if gender:
                query += " AND c.gender = ?"
                params.append(gender)

            query += " ORDER BY c.year DESC, c.round DESC"

            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_cutoff_trends(self, college_id, branch_id, category):
        """Get closing rank trend across years for a college/branch/category."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT year, closing_rank
                FROM cutoffs
                WHERE college_id = ? AND branch_id = ? AND category = ?
                  AND gender = 'ALL' AND round = 3
                ORDER BY year ASC
            ''', (college_id, branch_id, category))
            rows = cursor.fetchall()
            if not rows:
                # Fallback to any round
                cursor.execute('''
                    SELECT year, MAX(round) as round, closing_rank
                    FROM cutoffs
                    WHERE college_id = ? AND branch_id = ? AND category = ?
                    GROUP BY year
                    ORDER BY year ASC
                ''', (college_id, branch_id, category))
                rows = cursor.fetchall()
            return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_analytics(self, filters=None):
        """Return aggregated analytics data for charts."""
        filters = filters or {}
        category = filters.get('category', 'OPEN')
        if category and category.upper() != 'ALL':
            cat_filter = category.upper()
        else:
            cat_filter = 'OPEN'

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Cutoff trends: top 10 colleges x branches, last 3 years
            cursor.execute('''
                SELECT c.id as college_id, c.name, b.branch_name as branch,
                       cu.year, cu.category, cu.closing_rank
                FROM cutoffs cu
                JOIN colleges c ON cu.college_id = c.id
                JOIN branches b ON cu.branch_id = b.id
                WHERE cu.category = ? AND cu.gender = 'ALL' AND cu.round = 3
                ORDER BY c.avg_package_lpa DESC, cu.year ASC
                LIMIT 200
            ''', (cat_filter,))
            cutoff_trends = [dict(r) for r in cursor.fetchall()]

            # Fallback if specific category had few records
            if not cutoff_trends:
                cursor.execute('''
                    SELECT c.id as college_id, c.name, b.branch_name as branch,
                           cu.year, cu.category, cu.closing_rank
                    FROM cutoffs cu
                    JOIN colleges c ON cu.college_id = c.id
                    JOIN branches b ON cu.branch_id = b.id
                    WHERE cu.round = 3
                    ORDER BY c.avg_package_lpa DESC, cu.year ASC
                    LIMIT 200
                ''')
                cutoff_trends = [dict(r) for r in cursor.fetchall()]

            # Top colleges by placement
            cursor.execute('''
                SELECT c.name, AVG(p.avg_package_lpa) as avg_package,
                       AVG(p.placement_percentage) as placement_pct
                FROM placements p
                JOIN colleges c ON p.college_id = c.id
                GROUP BY c.id
                ORDER BY avg_package DESC
                LIMIT 15
            ''')
            top_colleges = [dict(r) for r in cursor.fetchall()]

            # Branch demand: average closing rank per branch
            cursor.execute('''
                SELECT b.branch_name as branch, COUNT(DISTINCT b.college_id) as college_count,
                       AVG(cu.closing_rank) as avg_closing_rank
                FROM cutoffs cu
                JOIN branches b ON cu.branch_id = b.id
                WHERE cu.category = ? AND cu.year = (SELECT MAX(year) FROM cutoffs)
                GROUP BY b.branch_name
                ORDER BY avg_closing_rank ASC
            ''', (cat_filter,))
            branch_demand = [dict(r) for r in cursor.fetchall()]

            if not branch_demand:
                cursor.execute('''
                    SELECT b.branch_name as branch, COUNT(DISTINCT b.college_id) as college_count,
                           AVG(cu.closing_rank) as avg_closing_rank
                    FROM cutoffs cu
                    JOIN branches b ON cu.branch_id = b.id
                    WHERE cu.year = (SELECT MAX(year) FROM cutoffs)
                    GROUP BY b.branch_name
                    ORDER BY avg_closing_rank ASC
                ''')
                branch_demand = [dict(r) for r in cursor.fetchall()]

            # College type distribution
            cursor.execute('''
                SELECT college_type as category, COUNT(*) as count,
                       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM colleges), 1) as percentage
                FROM colleges
                GROUP BY college_type
            ''')
            category_distribution = [dict(r) for r in cursor.fetchall()]

            return {
                'cutoff_trends': cutoff_trends,
                'top_colleges': top_colleges,
                'branch_demand': branch_demand,
                'category_distribution': category_distribution,
            }

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def get_comparison(self, college_ids, branch_ids=None, category='OPEN'):
        """Get comparison data for selected colleges."""
        if not college_ids:
            return []

        results = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for i, cid in enumerate(college_ids[:4]):
                cursor.execute("SELECT * FROM colleges WHERE id = ?", (cid,))
                college = cursor.fetchone()
                if not college:
                    continue
                college = dict(college)

                # Get branch info
                branch_id = branch_ids[i] if branch_ids and i < len(branch_ids) else None
                if branch_id:
                    cursor.execute("SELECT * FROM branches WHERE id = ?", (branch_id,))
                    branch = cursor.fetchone()
                    branch_name = branch['branch_name'] if branch else 'N/A'
                else:
                    cursor.execute("SELECT id, branch_name FROM branches WHERE college_id = ? LIMIT 1", (cid,))
                    b = cursor.fetchone()
                    branch_name = b['branch_name'] if b else 'N/A'
                    branch_id = b['id'] if b else None

                # Latest closing rank for that category
                closing_rank = None
                if branch_id:
                    cursor.execute('''
                        SELECT closing_rank FROM cutoffs
                        WHERE college_id = ? AND branch_id = ? AND category = ?
                        ORDER BY year DESC, round DESC LIMIT 1
                    ''', (cid, branch_id, category))
                    cr = cursor.fetchone()
                    if not cr:
                        cursor.execute('''
                            SELECT closing_rank FROM cutoffs
                            WHERE college_id = ? AND branch_id = ? AND category = 'OPEN'
                            ORDER BY year DESC, round DESC LIMIT 1
                        ''', (cid, branch_id))
                        cr = cursor.fetchone()
                    closing_rank = cr['closing_rank'] if cr else None

                # Latest placement
                cursor.execute('''
                    SELECT placement_percentage, avg_package_lpa, highest_package_lpa
                    FROM placements WHERE college_id = ? ORDER BY year DESC LIMIT 1
                ''', (cid,))
                p = cursor.fetchone()

                results.append({
                    'id': college['id'],
                    'name': college['name'],
                    'city': college['city'],
                    'state': college['state'],
                    'college_type': college['college_type'],
                    'fees': college['fees_per_year'],
                    'avg_package': college['avg_package_lpa'],
                    'highest_package': college['highest_package_lpa'],
                    'accreditation': college['accreditation'],
                    'naac_grade': college['naac_grade'],
                    'nba_accredited': college['nba_accredited'],
                    'branch': branch_name,
                    'closing_rank': closing_rank,
                    'placement_pct': p['placement_percentage'] if p else None,
                    'placement_avg_package': p['avg_package_lpa'] if p else None,
                    'placement_highest': p['highest_package_lpa'] if p else None,
                    'location': f"{college['city']}, {college['state']}",
                })

        return results

    # ------------------------------------------------------------------
    # Predictions
    # ------------------------------------------------------------------

    def save_prediction(self, student_data, preferences, result):
        """Save a prediction to the database. Returns prediction ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO predictions
                  (student_rank, category, gender, preferred_branches, preferred_cities, input_data, result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                student_data.get('merit_rank'),
                student_data.get('category'),
                student_data.get('gender'),
                json.dumps(preferences.get('preferred_branches', [])),
                json.dumps(preferences.get('preferred_cities', [])),
                json.dumps(student_data),
                json.dumps(result) if isinstance(result, dict) else str(result),
            ))
            conn.commit()
            return cursor.lastrowid

    def get_prediction_by_id(self, prediction_id):
        """Get a saved prediction by its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            try:
                data['input_data'] = json.loads(data['input_data']) if data['input_data'] else {}
                data['result'] = json.loads(data['result']) if data['result'] else {}
            except Exception:
                pass
            return data

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self):
        """Get high-level statistics for the home page."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as c FROM colleges")
            colleges_count = cursor.fetchone()['c']
            cursor.execute("SELECT COUNT(*) as c FROM branches")
            branches_count = cursor.fetchone()['c']
            cursor.execute("SELECT COUNT(*) as c FROM cutoffs")
            historical_records = cursor.fetchone()['c']
            return {
                'colleges_count': colleges_count,
                'branches_count': branches_count,
                'historical_records': historical_records,
            }

    def has_trained_model(self):
        """Check if ML model file exists."""
        model_path = os.getenv('MODEL_PATH', 'ml/model.pkl')
        return os.path.exists(model_path)
