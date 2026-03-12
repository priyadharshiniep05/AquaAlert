from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256))
    lat = db.Column(db.Float, default=19.0760)   # Default: Mumbai
    lng = db.Column(db.Float, default=72.8777)
    sms_opted_in = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    alerts = db.relationship('Alert', backref='user', lazy=True)
    reports = db.relationship('FloodReport', backref='user', lazy=True)

class WeatherData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    rainfall_mm = db.Column(db.Float)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    soil_saturation = db.Column(db.Float)
    river_level = db.Column(db.Float)
    risk_level = db.Column(db.String(10))  # LOW/MEDIUM/HIGH
    risk_score = db.Column(db.Float)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    severity = db.Column(db.String(10))
    message = db.Column(db.Text)
    sent_sms = db.Column(db.Boolean, default=False)
    sent_push = db.Column(db.Boolean, default=False)

class FloodReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    severity = db.Column(db.String(20))  # waterlogging/minor/severe
    description = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    verified = db.Column(db.Boolean, default=False)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    water_level_cm = db.Column(db.Float)
    flow_rate = db.Column(db.Float)
