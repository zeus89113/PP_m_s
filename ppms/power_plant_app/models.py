from . import db
from datetime import datetime

notification_reads = db.Table('notification_reads',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('notification_id', db.Integer, db.ForeignKey('notification.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='operator') # admin, operator, safety, environment
    read_notifications = db.relationship('Notification', secondary=notification_reads, back_populates='read_by_users')

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class PlantReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_name = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(50))
    power_output_mw = db.Column(db.Float)
    temperature_c = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Report {self.module_name} @ {self.timestamp}>'
    

class MaintenanceSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_name = db.Column(db.String(80), nullable=False)
    scheduled_for_datetime = db.Column(db.DateTime, nullable=False)
    scheduled_by_username = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Maintenance for {self.module_name} on {self.scheduled_for_datetime}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(300), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    read_by_users = db.relationship('User', secondary=notification_reads, back_populates='read_notifications')

    def __repr__(self):
        return f'<Notification: {self.message[:30]}...>'