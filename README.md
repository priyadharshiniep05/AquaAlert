# AquaAlert

**AquaAlert** is an AI-powered hyperlocal flood prediction and community alert system designed for municipalities, emergency responders, and community members. It uses a combination of satellite data, real-time IoT water sensors, and machine learning to predict flood risk and notify communities before disaster strikes.

![AquaAlert Preview](https://via.placeholder.com/800x400.png?text=AquaAlert+Dashboard)

## Features
- **Real-Time Dashboard**: See rainfall, river levels, and risk scores at a glance.
- **AI Flood Prediction**: A Random Forest model evaluates real-time data to output a risk probability.
- **SMS & Push Alerts**: Powered by Twilio, alerting users even with limited connectivity (satellite fallback).
- **Live Maps**: Integration with Leaflet.js to visualize flood zones, shelters, safe routes, and IoT sensors.
- **Community Crowdsourcing**: Users can submit geo-tagged flood reports to improve situational awareness.
- **Progressive Web App (PWA)**: Installable on mobile devices (iOS/Android) with offline caching capabilities.

## Tech Stack
- **Backend:** Python, Flask, Flask-SQLAlchemy, APScheduler
- **Machine Learning:** Scikit-Learn (RandomForestClassifier), Pandas, NumPy
- **Frontend:** Vanilla HTML/CSS/JS, Chart.js, Leaflet.js
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **External Services:** Twilio API (SMS Alerts), OpenWeather API (Weather Data)

## Getting Started

### Prerequisites
- Python 3.10+
- `pip`

### Installation

1. **Clone the repository** (if applicable) or navigate to the project directory:
   ```bash
   cd AquaAlert
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Copy the example environment file and fill in your details:
   ```bash
   cp .env.example .env
   ```
   *Note: If `OPENWEATHER_API_KEY` or `TWILIO` variables are empty, the app will run in "Simulation Mode" generating mock data and simulating SMS sends in the server logs.*

5. **Initialize Database:**
   The application automatically initializes the database (`instance/aquaalert.db`) internally on the first run. However, if you need to manually init or debug:
   ```python
   # inside python shell
   from app import app, db, seed_demo_data
   with app.app_context():
       db.create_all()
       seed_demo_data()
   ```

6. **Run the Application:**
   ```bash
   python app.py
   # OR
   FLASK_APP=app.py FLASK_ENV=development flask run
   ```

7. **Access the App:**
   Open your browser and navigate to `http://127.0.0.1:5000`

### Demo Credentials
To login for judging or demo purposes, create an account, or the app will automatically allow you to sign up on the `/signup` page.

### Mock Data & Offline Mode
For hackathons, the ML model generates mock training data (`ml_model.py`) to bypass the need for massive real-world datasets initially. The `app.py` has generators for fake weather data and sensory input when APIs are unreachable.

The frontend includes a Service Worker (`static/js/sw.js`) allowing the page to load even if the user drops off the network.

## Project Structure
- `app.py`: Main Flask application, routes, APIs, and background scheduler.
- `database.py`: SQLAlchemy database models.
- `ml_model.py`: Generates synthetic data, trains, and exposes the `FloodPredictor`.
- `alert_engine.py`: Handles Twilio SMS logic and distance radius calculations.
- `static/`: CSS styling, JS logic, PWA `manifest.json`, and icons.
- `templates/`: Jinja2 HTML templates.
- `data/`: JSON static files (shelters, contacts) and the saved ML model `.pkl`.
