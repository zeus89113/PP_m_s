from . import db
from datetime import datetime

class PlantReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_name = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(50))
    power_output_mw = db.Column(db.Float)
    temperature_c = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Report {self.module_name} @ {self.timestamp}>'