import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create a minimal Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Configure database connection using the new environment variables
pguser = os.environ.get("PGUSER")
pgpassword = os.environ.get("PGPASSWORD")
pghost = os.environ.get("PGHOST")
pgport = os.environ.get("PGPORT")
pgdatabase = os.environ.get("PGDATABASE")

# Construct the database URL
if pguser and pgpassword and pghost and pgport and pgdatabase:
    database_url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdatabase}"
    logger.info(f"Constructed new database URL")
else:
    database_url = os.environ.get("DATABASE_URL")
    logger.info(f"Using DATABASE_URL from environment")

logger.info(f"Database URL has a length of: {len(database_url)}")
logger.info(f"Host: {pghost}, Port: {pgport}, Database: {pgdatabase}, User: {pguser}")

# Configure Flask app with the database URL
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_timeout": 30,
    "pool_size": 10,
    "max_overflow": 5
}

# Initialize the database with the Flask app
db.init_app(app)

# Define our models (similar to models.py)
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
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
        return f'<Cattle {self.cattle_type}>'

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OTP {self.otp} for User {self.user_id}>'

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
        return [symptom.strip() for symptom in self.symptoms.split(',')]
    
    def get_precautions_list(self):
        return [precaution.strip() for precaution in self.precautions.split(',')]

# Create the database tables and add sample data
def init_tables_with_sample_data():
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Add sample veterinarian data if none exists
            if not Veterinarian.query.first():
                logger.info("Adding sample veterinarian data")
                sample_vets = [
                    Veterinarian(name="Dr. John Smith", specialization="Dairy Cattle", phone="9876543210", location="City Center", address="123 Main St", latitude=28.6139, longitude=77.2090),
                    Veterinarian(name="Dr. Maria Garcia", specialization="Beef Cattle", phone="9876543211", location="North District", address="456 Oak Ave", latitude=28.7041, longitude=77.1025),
                    Veterinarian(name="Dr. Rajesh Kumar", specialization="All Cattle", phone="9876543212", location="South District", address="789 Pine Rd", latitude=28.5355, longitude=77.2410)
                ]
                db.session.add_all(sample_vets)
                
            # Add disease data if none exists
            if not CattleDisease.query.first():
                logger.info("Adding sample disease data")
                diseases = [
                    CattleDisease(
                        name="Mastitis",
                        symptoms="Swollen udder,Redness,Pain,Abnormal milk,Reduced milk production,Fever",
                        description="Inflammation of the mammary gland and udder tissue",
                        precautions="Keep udders clean,Regular milking,Proper milking technique,Early treatment",
                        severity="High"
                    ),
                    CattleDisease(
                        name="Foot and Mouth Disease",
                        symptoms="Fever,Blisters on mouth,Blisters on feet,Reduced appetite,Excessive salivation,Lameness",
                        description="Viral disease affecting cloven-hoofed animals",
                        precautions="Vaccination,Quarantine affected animals,Proper sanitation,Movement restrictions",
                        severity="High"
                    ),
                    CattleDisease(
                        name="Bloat",
                        symptoms="Swollen left abdomen,Difficulty breathing,Discomfort,Excessive salivation,Rapid breathing,Lack of rumination",
                        description="Accumulation of gas in the rumen that cannot be expelled",
                        precautions="Gradual diet changes,Avoid wet legumes,Provide dry hay,Monitor grazing",
                        severity="Medium"
                    ),
                    CattleDisease(
                        name="Milk Fever",
                        symptoms="Weakness,Lowered body temperature,Difficulty standing,Muscle tremors,Reduced milk production,Loss of appetite",
                        description="Calcium deficiency occurring at calving",
                        precautions="Proper nutrition,Calcium supplements,Monitor transition cows,Reduce high potassium feeds",
                        severity="Medium"
                    ),
                    CattleDisease(
                        name="Bovine Respiratory Disease",
                        symptoms="Coughing,Nasal discharge,Fever,Rapid breathing,Reduced appetite,Lethargy",
                        description="Complex of respiratory diseases affecting cattle",
                        precautions="Vaccination,Proper ventilation,Reduce stress,Early treatment",
                        severity="High"
                    )
                ]
                db.session.add_all(diseases)
                
            # Commit all changes
            db.session.commit()
            logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Initializing database tables with sample data...")
    init_tables_with_sample_data()