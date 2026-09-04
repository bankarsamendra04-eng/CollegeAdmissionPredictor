# 🎓 AI College Admission Predictor

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-000000.svg?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.0+-F7931E.svg?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Repository](https://img.shields.io/badge/GitHub-CollegeAdmissionPredictor-181717?logo=github)](https://github.com/bankarsamendra04-eng/CollegeAdmissionPredictor)

An intelligent, data-driven web application designed to help engineering aspirants predict their probability of admission into top colleges across Maharashtra (MHT-CET / JEE Main). Powered by machine learning classification models, multi-year historical cutoff analytics, and automated preference matching.

🔗 **GitHub Repository:** [https://github.com/bankarsamendra04-eng/CollegeAdmissionPredictor](https://github.com/bankarsamendra04-eng/CollegeAdmissionPredictor)

---

## 🌟 Key Features

- **🔮 Smart Admission Predictor:** 5-step guided wizard that evaluates student merit rank, reservation category, gender, branch choices, tuition budget, and preferred locations.
- **📊 Probability Classification:** Classifies colleges into **Safe (≥75%)**, **Moderate (40–74%)**, **Dream (15–39%)**, and **Unlikely (<15%)** chances using calibrated ML models and historical cutoff trend analysis.
- **🏫 College Directory & Advanced Filtering:** Search and filter 35+ top institutions across Maharashtra by city, district, college type (Government, Autonomous, Private), NAAC grade, tuition fees, and branch offerings.
- **⚖️ Side-by-Side Comparison:** Compare up to 4 institutions simultaneously across cutoffs, seat intake, average & highest packages, accreditation, and fees.
- **📈 Real-Time Analytics Dashboard:** Interactive Chart.js visualizations showing branch popularity, category cutoff distributions, college type allocations, and fee vs. placement correlations.
- **📄 Report Generation:** Instantly view and export personalized admission recommendation reports.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.8+, Flask, RESTful API |
| **Machine Learning** | scikit-learn, Random Forest Classifier, Gradient Boosting, CalibratedClassifierCV |
| **Data Processing** | pandas, numpy |
| **Database** | SQLite3 with auto-initialization from structured CSV datasets |
| **Frontend** | HTML5, CSS3 (Modern Responsive Theme), Vanilla JavaScript (ES6+), Jinja2 |
| **Data Visualization** | Chart.js 4.x, Font Awesome 6 |
| **Testing** | pytest (Unit & Integration Test Suite) |

---

## 📂 Project Structure

```text
CollegeAdmissionPredictor/
├── app.py                      # Flask application entry point & API routes
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # Comprehensive documentation
├── generate_data.py            # Synthetic & real data generator script
├── database/                   # Database access layer
│   ├── __init__.py
│   ├── database.py             # SQLite DatabaseManager with full CRUD & search
│   └── schema.sql              # Database relational schema
├── data/                       # Initial seeding CSV datasets
│   ├── colleges.csv            # 35+ Maharashtra engineering institutions
│   ├── branches.csv            # Engineering disciplines & seat intakes
│   ├── cutoffs.csv             # Multi-year category-wise opening/closing ranks
│   └── placements.csv          # Placement statistics & recruiter metrics
├── ml/                         # Machine learning pipeline
│   ├── __init__.py
│   ├── preprocess.py           # Feature engineering & preprocessing pipeline
│   ├── train.py                # Model training, validation, & calibration script
│   ├── predict.py              # Real-time inference & fallback heuristic engine
│   └── model.pkl               # Calibrated predictive model artifact
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Global navigation, footer, & theme skeleton
│   ├── index.html              # Landing page with hero & quick stats
│   ├── predictor.html          # 5-step interactive admission prediction wizard
│   ├── colleges.html           # College directory with multi-filter sidebar
│   ├── compare.html            # College comparison matrix
│   ├── analytics.html          # Dynamic charts & trend visualizations
│   ├── about.html              # Methodology, algorithms, & GitHub info
│   └── disclaimer.html         # Legal & data disclaimer notice
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css           # Clean, modern responsive design stylesheet
│   └── js/
│       ├── app.js              # Global utilities, navigation, and modal helpers
│       ├── predictor.js        # Form validation, API integration & card renderer
│       ├── colleges.js         # Search, filter, pagination, & modal logic
│       └── analytics.js        # Chart.js initialization & dynamic data bindings
└── tests/                      # Automated test suite
    ├── __init__.py
    ├── test_api.py             # End-to-end REST API endpoint tests
    └── test_prediction.py      # ML pipeline, heuristic fallback & logic tests
```

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/bankarsamendra04-eng/CollegeAdmissionPredictor.git
cd CollegeAdmissionPredictor
```

### 2. Set Up Virtual Environment
```bash
# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\activate

# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy sample configuration
cp .env.example .env
```

### 5. Initialize Database & Train Model
The database and ML model automatically initialize on server startup. To train manually:
```bash
python ml/train.py
```

### 6. Run the Application
```bash
python app.py
```
Open your browser and navigate to: **`http://localhost:5000`**

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stats` | System metrics (total colleges, branches, historical cutoff records) |
| `GET` | `/api/colleges` | Search & filter colleges (supports city, branch, type, fees, NAAC, sorting) |
| `GET` | `/api/college/<id>` | Full college profile, branches, fees, placements, and cutoffs |
| `GET` | `/api/branches` | List all engineering branches or filter by college |
| `GET` | `/api/categories` | List available reservation categories (`OPEN`, `OBC`, `SC`, `ST`, `EWS`, `TFWS`, etc.) |
| `GET` | `/api/cutoffs` | Query historical cutoff records by college, branch, category, year, round |
| `GET` | `/api/analytics` | Aggregated analytics dataset for Chart.js dashboard |
| `POST` | `/api/predict` | Main prediction endpoint: takes rank, category, branch preferences, budget |
| `POST` | `/api/compare` | Compare 2 to 4 colleges by ID across multiple parameters |
| `GET` | `/api/export/<id>` | Export prediction summary |

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:

```bash
pytest
```

Output:
```text
============================= test session starts =============================
collected 30 items

tests/test_api.py ...............                                        [ 50%]
tests/test_prediction.py ...............                                 [100%]

============================== 30 passed in 4.64s ==============================
```

---

## 💡 How the Prediction Engine Works

1. **Feature Encoding & Normalization:** Standardizes user merit rank, category quota, gender, and branch preferences.
2. **Machine Learning Model:** Evaluates features using an ensemble classifier calibrated with `CalibratedClassifierCV` to output well-calibrated admission probabilities.
3. **Multi-Year Trend Analysis:** Analyzes cutoff fluctuations over the last 3 years to account for rising/easing demand.
4. **Weighted Recommendation Score:**
   $$\text{Score} = (w_1 \times \text{Admission Prob}) + (w_2 \times \text{Placement Index}) + (w_3 \times \text{Accreditation}) + (w_4 \times \text{Location Match})$$
5. **Tier Categorization:** Sorts recommendations into **Safe**, **Moderate**, and **Dream** categories to give students a balanced choice list.

---

## 🤝 Contributing

Contributions are welcome! If you'd like to improve the prediction algorithms, add more college datasets, or enhance the UI:

1. Fork the repository: [https://github.com/bankarsamendra04-eng/CollegeAdmissionPredictor](https://github.com/bankarsamendra04-eng/CollegeAdmissionPredictor)
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## ⚖️ Disclaimer

*The predictions generated by this tool are statistical estimates based on historical cutoffs and trends. Cutoffs vary each year depending on student preferences, exam difficulty, and seat matrices. Official State CET Cell / DTE notifications should always be consulted for final admissions.*
