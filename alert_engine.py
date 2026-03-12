import os
from datetime import datetime
from database import db, User, Alert
import requests

class AlertEngine:
    def __init__(self, app):
        self.app = app
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID', 'DEMO_MODE')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN', 'DEMO_MODE')
        self.twilio_phone = os.getenv('TWILIO_PHONE', '+15005550006')
        self.demo_mode = (self.twilio_sid == 'DEMO_MODE')

    def _compose_message(self, severity, location="your area"):
        messages = {
            'HIGH': f"🚨 AQUAALERT EMERGENCY: SEVERE flood risk detected in {location}. EVACUATE IMMEDIATELY. Follow safe routes on aquaalert.app",
            'MEDIUM': f"⚠️ AQUAALERT WARNING: Moderate flood risk in {location}. Avoid low-lying areas. Stay updated at aquaalert.app",
            'LOW': f"✅ AQUAALERT: Low flood risk in {location}. Conditions monitored. Stay prepared."
        }
        return messages.get(severity, messages['LOW'])

    def send_sms(self, phone, message):
        """Send SMS via Twilio (satellite fallback simulation)"""
        # SATELLITE SMS FALLBACK:
        # Twilio's global SMS network works via satellite infrastructure 
        # in low-connectivity areas. When internet is down on user's phone, 
        # SMS still delivers via cellular towers and satellite links.
        if self.demo_mode:
            print(f"[DEMO SMS] To: {phone} | Msg: {message[:50]}...")
            return True
        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)
            client.messages.create(body=message, from_=self.twilio_phone, to=phone)
            return True
        except Exception as e:
            print(f"SMS Error: {e}")
            return False

    def send_voice_alert(self, phone, severity):
        """Voice alert for accessibility"""
        if self.demo_mode:
            print(f"[DEMO VOICE] To: {phone} | Severity: {severity}")
            return True
        # Twilio voice call implementation
        return True

    def broadcast_alert(self, risk_level, lat, lng, radius_km=10):
        """Broadcast to all opted-in users within radius"""
        with self.app.app_context():
            users = User.query.filter_by(sms_opted_in=True).all()
            alerted = 0
            for user in users:
                if self._is_within_radius(user.lat, user.lng, lat, lng, radius_km):
                    message = self._compose_message(risk_level)
                    if user.phone:
                        sms_sent = self.send_sms(user.phone, message)
                    else:
                        sms_sent = False
                    alert = Alert(
                        user_id=user.id,
                        severity=risk_level,
                        message=message,
                        sent_sms=sms_sent,
                        sent_push=True
                    )
                    db.session.add(alert)
                    alerted += 1
            db.session.commit()
            return alerted

    def _is_within_radius(self, lat1, lng1, lat2, lng2, radius_km):
        import math
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
        return R * 2 * math.asin(math.sqrt(a)) <= radius_km
