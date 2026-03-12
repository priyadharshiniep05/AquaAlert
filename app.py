from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import requests, json, random, os
from dotenv import load_dotenv
from database import db, User, WeatherData, Alert, FloodReport, SensorReading
from ml_model import FloodPredictor
from alert_engine import AlertEngine
import numpy as np

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'aquaalert-dev-secret-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aquaalert.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

predictor = FloodPredictor()
alert_engine = None  # initialized after app context

OPENWEATHER_KEY = os.getenv('OPENWEATHER_API_KEY', '')

# ─── Mock Data Generators ───────────────────────────────────

def get_mock_weather():
    """Simulated weather when API not available"""
    return {
        'rainfall_mm': random.uniform(0, 120),
        'temperature': random.uniform(20, 38),
        'humidity': random.uniform(50, 99),
        'soil_saturation': random.uniform(0.1, 1.0),
        'river_level': random.uniform(0.5, 9.5),
        'description': random.choice(['Heavy Rain', 'Thunderstorm', 'Light Rain', 'Overcast']),
        'wind_speed': random.uniform(5, 45),
        'source': 'simulation'
    }

def get_real_weather(lat, lng):
    if not OPENWEATHER_KEY:
        return get_mock_weather()
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={OPENWEATHER_KEY}&units=metric"
        r = requests.get(url, timeout=5)
        data = r.json()
        return {
            'rainfall_mm': data.get('rain', {}).get('1h', random.uniform(0, 80)),
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'soil_saturation': random.uniform(0.3, 0.9),
            'river_level': random.uniform(1, 8),
            'description': data['weather'][0]['description'].title(),
            'wind_speed': data['wind']['speed'],
            'source': 'openweather'
        }
    except:
        return get_mock_weather()

def simulate_iot_sensors():
    """Mock IoT water level sensors"""
    sensor_locations = [
        {'id': 'S001', 'lat': 19.0760, 'lng': 72.8777, 'name': 'Dharavi'},
        {'id': 'S002', 'lat': 19.0330, 'lng': 73.0297, 'name': 'Vashi'},
        {'id': 'S003', 'lat': 18.9220, 'lng': 72.8347, 'name': 'Colaba'},
        {'id': 'S004', 'lat': 19.1136, 'lng': 72.8697, 'name': 'Andheri'},
        {'id': 'S005', 'lat': 19.1663, 'lng': 72.8526, 'name': 'Borivali'},
    ]
    return [{'sensor_id': s['id'], 'lat': s['lat'], 'lng': s['lng'], 
             'name': s['name'], 'water_level_cm': round(random.uniform(5, 180), 1),
             'flow_rate': round(random.uniform(0.1, 5.0), 2),
             'timestamp': datetime.utcnow().isoformat()} for s in sensor_locations]

def get_flood_zones():
    """Mock flood-prone zones for map overlay"""
    return [
        {"id": 1, "name": "Dharavi Low Zone", "lat": 19.0400, "lng": 72.8530, "risk": "HIGH", "radius": 800},
        {"id": 2, "name": "Mithi River Bank", "lat": 19.0665, "lng": 72.8720, "risk": "HIGH", "radius": 600},
        {"id": 3, "name": "Kurla West", "lat": 19.0700, "lng": 72.8800, "risk": "MEDIUM", "radius": 500},
        {"id": 4, "name": "Andheri East", "lat": 19.1136, "lng": 72.8697, "risk": "MEDIUM", "radius": 400},
        {"id": 5, "name": "Bandra Reclamation", "lat": 19.0550, "lng": 72.8250, "risk": "LOW", "radius": 300},
    ]

def get_safe_routes():
    return [
        {"name": "Route A - Dharavi to Sion", "waypoints": [[19.040, 72.853], [19.046, 72.862], [19.053, 72.869]]},
        {"name": "Route B - Kurla Bypass", "waypoints": [[19.070, 72.880], [19.075, 72.872], [19.080, 72.865]]},
    ]

# ─── Scheduled Jobs ─────────────────────────────────────────

def scheduled_prediction_job():
    with app.app_context():
        lat, lng = 19.0760, 72.8777
        weather = get_real_weather(lat, lng)
        prediction = predictor.predict(
            weather['rainfall_mm'], weather['humidity'],
            weather['soil_saturation'], weather['river_level'], weather['temperature']
        )
        wd = WeatherData(lat=lat, lng=lng, **{k: weather[k] for k in 
              ['rainfall_mm','temperature','humidity','soil_saturation','river_level']},
              risk_level=prediction['risk_level'], risk_score=prediction['risk_score'])
        db.session.add(wd)
        db.session.commit()
        if prediction['risk_level'] in ['HIGH', 'MEDIUM']:
            global alert_engine
            if alert_engine:
                alert_engine.broadcast_alert(prediction['risk_level'], lat, lng)

# ─── Auth Routes ─────────────────────────────────────────────

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        if User.query.filter_by(email=data['email']).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('signup'))
        user = User(
            name=data['name'], email=data['email'],
            phone=data.get('phone', ''),
            password_hash=generate_password_hash(data['password']),
            lat=float(data.get('lat', 19.0760)),
            lng=float(data.get('lng', 72.8777)),
            sms_opted_in=bool(data.get('sms_optin'))
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Welcome to AquaAlert! 🌊', 'success')
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ─── Page Routes ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    latest = WeatherData.query.order_by(WeatherData.timestamp.desc()).first()
    recent_reports = FloodReport.query.order_by(FloodReport.timestamp.desc()).limit(5).all()
    sensors = simulate_iot_sensors()
    return render_template('dashboard.html', latest=latest, reports=recent_reports, sensors=sensors)

@app.route('/map')
@login_required
def map_view():
    return render_template('map.html')

@app.route('/reports')
@login_required
def reports():
    all_reports = FloodReport.query.order_by(FloodReport.timestamp.desc()).all()
    return render_template('reports.html', reports=all_reports)

@app.route('/preparedness')
@login_required
def preparedness():
    with open('data/shelters.json') as f:
        shelters = json.load(f)
    with open('data/emergency_contacts.json') as f:
        contacts = json.load(f)
    return render_template('preparedness.html', shelters=shelters, contacts=contacts)

# ─── API Endpoints ───────────────────────────────────────────

@app.route('/api/predict', methods=['POST'])
def api_predict():
    d = request.json
    lat = d.get('lat', 19.0760)
    lng = d.get('lng', 72.8777)
    weather = get_real_weather(lat, lng)
    result = predictor.predict(
        d.get('rainfall_mm', weather['rainfall_mm']),
        d.get('humidity', weather['humidity']),
        d.get('soil_saturation', weather['soil_saturation']),
        d.get('river_level', weather['river_level']),
        d.get('temperature', weather['temperature'])
    )
    return jsonify({**weather, **result, 'lat': lat, 'lng': lng, 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/weather/current')
def api_weather():
    lat = float(request.args.get('lat', 19.0760))
    lng = float(request.args.get('lng', 72.8777))
    weather = get_real_weather(lat, lng)
    prediction = predictor.predict(weather['rainfall_mm'], weather['humidity'],
                                   weather['soil_saturation'], weather['river_level'], weather['temperature'])
    return jsonify({**weather, **prediction, 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/weather/history')
@login_required
def api_weather_history():
    hours = int(request.args.get('hours', 24))
    since = datetime.utcnow() - timedelta(hours=hours)
    data = WeatherData.query.filter(WeatherData.timestamp >= since).order_by(WeatherData.timestamp.asc()).all()
    if not data:
        # Return mock history
        history = []
        for i in range(24):
            t = datetime.utcnow() - timedelta(hours=24-i)
            r = random.uniform(5, 100)
            history.append({'timestamp': t.isoformat(), 'rainfall_mm': round(r,1),
                            'risk_score': round(min(r/1.5, 100), 1),
                            'risk_level': 'HIGH' if r > 70 else 'MEDIUM' if r > 35 else 'LOW'})
        return jsonify(history)
    return jsonify([{'timestamp': d.timestamp.isoformat(), 'rainfall_mm': d.rainfall_mm,
                     'risk_score': d.risk_score, 'risk_level': d.risk_level} for d in data])

@app.route('/api/flood-zones')
def api_flood_zones():
    return jsonify(get_flood_zones())

@app.route('/api/safe-routes')
def api_safe_routes():
    return jsonify(get_safe_routes())

@app.route('/api/sensors')
def api_sensors():
    return jsonify(simulate_iot_sensors())

@app.route('/api/reports', methods=['GET', 'POST'])
def api_reports():
    if request.method == 'POST':
        d = request.json
        report = FloodReport(
            user_id=current_user.id if current_user.is_authenticated else None,
            lat=d['lat'], lng=d['lng'],
            severity=d['severity'],
            description=d['description'],
            image_url=d.get('image_url', '')
        )
        db.session.add(report)
        db.session.commit()
        
        # CROWDSOURCING -> ML FEEDBACK LOOP (Implementation note step 4)
        # We can implement a cron job here or just store it. The job could export 
        # FloodReport table to CSV and retrain model with verified reports.
        
        return jsonify({'status': 'success', 'id': report.id})
    reports = FloodReport.query.order_by(FloodReport.timestamp.desc()).limit(50).all()
    return jsonify([{'id': r.id, 'lat': r.lat, 'lng': r.lng, 'severity': r.severity,
                     'description': r.description, 'timestamp': r.timestamp.isoformat(),
                     'upvotes': r.upvotes, 'verified': r.verified} for r in reports])

@app.route('/api/reports/<int:report_id>/upvote', methods=['POST'])
def upvote_report(report_id):
    report = FloodReport.query.get_or_404(report_id)
    report.upvotes += 1
    db.session.commit()
    return jsonify({'upvotes': report.upvotes})

@app.route('/api/alerts/send', methods=['POST'])
@login_required
def send_alert():
    d = request.json
    count = alert_engine.broadcast_alert(d['risk_level'], d['lat'], d['lng'], d.get('radius', 10))
    return jsonify({'alerted': count, 'status': 'sent'})

@app.route('/api/alert-test')
@login_required  
def test_alert():
    if current_user.phone:
        msg = alert_engine._compose_message('HIGH', 'your area')
        alert_engine.send_sms(current_user.phone, msg)
        return jsonify({'status': 'sent', 'demo': alert_engine.demo_mode})
    return jsonify({'status': 'no_phone'})

@app.route('/api/stats')
def api_stats():
    return jsonify({
        'total_users': User.query.count(),
        'total_alerts': Alert.query.count(),
        'total_reports': FloodReport.query.count(),
        'active_sensors': 5,
        'last_updated': datetime.utcnow().isoformat()
    })

# ─── PWA Manifest & Service Worker ──────────────────────────

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def service_worker():
    return app.send_static_file('js/sw.js')

# ─── App Init ────────────────────────────────────────────────

def seed_demo_data():
    """Add mock reports for demo"""
    if FloodReport.query.count() == 0:
        mock_reports = [
            {'lat': 19.0400, 'lng': 72.8530, 'severity': 'severe', 'description': 'Road completely flooded 3ft deep. Avoid Dharavi main road.', 'upvotes': 23, 'verified': True},
            {'lat': 19.0665, 'lng': 72.8720, 'severity': 'waterlogging', 'description': 'Knee-deep water near Mithi River bridge.', 'upvotes': 15, 'verified': True},
            {'lat': 19.1136, 'lng': 72.8697, 'severity': 'minor', 'description': 'Water logging at Andheri station exit.', 'upvotes': 8, 'verified': False},
        ]
        for r in mock_reports:
            db.session.add(FloodReport(**r))
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_demo_data()
    alert_engine = AlertEngine(app)
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_prediction_job, 'interval', minutes=10)
    scheduler.start()
    app.run(debug=True, host='0.0.0.0', port=5000)
