import logging
import os
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

def init_db(app):
    """Initialize the database with the Flask app."""
    # Use SQLite for reliability
    db_path = os.path.join(os.getcwd(), 'cattle_health.db')
    database_url = f"sqlite:///{db_path}"
    
    # Update app config with the database URL
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    
    # Set SQLAlchemy options
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
    }

    logger.info(f"Connecting to SQLite database at: {db_path}")
    db.init_app(app)
    
    try:
        # Create tables and add sample data
        with app.app_context():
            # Import models here to avoid circular imports
            from models import User, Cattle, OTP, Veterinarian, CattleDisease
            
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