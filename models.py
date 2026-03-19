from datetime import datetime
from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cattle = db.relationship('Cattle', backref='owner', lazy=True)
    otps = db.relationship('OTP', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.name}>'

class Cattle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    animal_type = db.Column(db.String(20), nullable=True)  # 'Cow/Oxen' or 'Buffalo'
    cattle_type = db.Column(db.String(50), nullable=False)  # Specific breed
    age = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    heart_rate = db.Column(db.Integer, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    milk_yield = db.Column(db.Float, nullable=True)
    symptoms = db.Column(db.Text, nullable=False)
    photo_filename = db.Column(db.String(255), nullable=True)  # Store filename of uploaded photo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Cattle {self.id} ({self.animal_type}: {self.cattle_type}) owned by User {self.user_id}>'

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OTP for User {self.user_id}>'

class Veterinarian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(15), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    def __repr__(self):
        return f'<Veterinarian {self.name}>'

class CattleDisease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)  # Comma-separated list of symptoms
    description = db.Column(db.Text, nullable=False)
    precautions = db.Column(db.Text, nullable=False)  # Comma-separated list of precautions
    severity = db.Column(db.String(20), nullable=False)  # Low, Medium, High
    
    def __repr__(self):
        return f'<CattleDisease {self.name}>'
    
    def get_symptoms_list(self):
        return self.symptoms.split(',')
    
    def get_precautions_list(self):
        return self.precautions.split(',')
