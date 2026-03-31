# HealthTrack — Your Health, Simplified

A comprehensive health tracking web application built with **FastAPI**, **SQLAlchemy**, and modern **HTML/CSS/JavaScript**. Track 11 health metrics in one unified dashboard with interactive visualizations.

![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003b57?style=flat-square&logo=sqlite&logoColor=white)

## Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Water Tracker** | Log glasses, track daily intake toward your 8-glass goal |
| 2 | **Calorie Counter** | Log meals by type with macros (protein, carbs, fat) |
| 3 | **Exercise Log** | Record workouts, duration, and calories burned |
| 4 | **Medication Reminders** | Track doses, pill inventory, and refill alerts |
| 5 | **BMI Calculator** | Dynamic color-coded gauge (underweight → healthy → obese) |
| 6 | **Sleep Tracker** | Log hours and rate quality (1-5 stars) |
| 7 | **PDF Reports** | Download professional weekly health reports |
| 8 | **Activity Dashboard** | Apple Watch-inspired rings for daily progress |
| 9 | **Consistency Calendar** | GitHub-style heatmap for health streaks |
| 10 | **Period Tracker** | Phase-synced UI with cycle tracking |
| 11 | **Emergency Card** | One-tap allergy card with emergency contacts |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + FastAPI |
| Frontend | HTML5, CSS3, JavaScript |
| Database | SQLite + SQLAlchemy ORM |
| Charts | Chart.js |
| Icons | Lucide Icons |
| Reports | ReportLab (PDF generation) |
| Auth | JWT tokens + bcrypt password hashing |

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/healthtrack.git
cd healthtrack
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
uvicorn main:app --reload
```

Open **http://localhost:8000** in your browser.

## Project Structure

```
├── main.py                 # FastAPI app entry point
├── database.py             # SQLAlchemy database setup
├── models.py               # Database models (User, Logs, etc.)
├── auth.py                 # Authentication utilities (JWT, bcrypt)
├── routers/
│   ├── auth_routes.py      # Login, Register, Password Reset
│   └── api_routes.py       # All health tracking API endpoints
├── templates/
│   ├── base.html           # Base template with navbar & footer
│   ├── landing.html        # Landing page with feature showcase
│   ├── login.html          # Login page
│   ├── register.html       # Multi-step registration
│   ├── dashboard.html      # Main dashboard with all features
│   ├── forgot_password.html
│   └── reset_password.html
├── static/
│   ├── css/style.css       # Complete stylesheet
│   └── js/app.js           # Frontend interactivity
├── requirements.txt
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/water` | Log water intake |
| POST | `/api/calories` | Log a meal |
| POST | `/api/exercise` | Log exercise |
| POST | `/api/sleep` | Log sleep |
| POST | `/api/mood` | Log mood & energy |
| POST | `/api/period` | Log period entry |
| POST | `/api/medications` | Add medication |
| POST | `/api/medications/{id}/take` | Mark medication as taken |
| POST | `/api/allergies` | Add allergy info |
| GET | `/api/dashboard/summary` | Today's dashboard data |
| GET | `/api/dashboard/trends` | 7-day trend data |
| GET | `/api/dashboard/heatmap` | 90-day consistency heatmap |
| GET | `/api/report/pdf` | Download weekly PDF report |

## Screenshots

The application features:
- **Landing page** with animated hero section and interactive feature cards
- **Multi-step registration** with live BMI preview
- **Dashboard** with Apple Watch-style activity rings
- **GitHub-style** consistency heatmap
- **Phase-synced UI** for period tracking
- **Emergency card** modal for allergy information

## License

MIT License — feel free to use this project for learning and portfolio purposes.
