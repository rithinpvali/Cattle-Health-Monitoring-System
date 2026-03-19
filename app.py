import os
import logging
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


if not os.environ.get("TWILIO_ACCOUNT_SID"):
    os.environ["TWILIO_ACCOUNT_SID"] = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_AUTH_TOKEN"):
    os.environ["TWILIO_AUTH_TOKEN"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_PHONE_NUMBER"):
    os.environ["TWILIO_PHONE_NUMBER"] = "+10000000000"                    

from database import db, init_db
from models import User, Cattle, OTP, Veterinarian, CattleDisease
from otp_utils import generate_otp, send_otp
from disease_predictor import predict_disease
from vet_finder import find_nearby_vets

try:
    
    logger.info("Initializing database...")
    init_db(app)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name or not phone:
            flash('Please provide both name and phone number', 'danger')
            return render_template('login.html')
        
        if not phone.isdigit() or len(phone) != 10:
            flash('Please provide a valid 10-digit phone number', 'danger')
            return render_template('login.html')
        
        # Check if user exists, create if not
        user = User.query.filter_by(phone=phone).first()
        if not user:
            user = User(name=name, phone=phone)
            db.session.add(user)
            db.session.commit()
        
        # Generate and save OTP
        otp_value = generate_otp()
        otp_record = OTP(user_id=user.id, otp=otp_value)
        db.session.add(otp_record)
        db.session.commit()
        
        # In a real application, we would send the OTP via SMS
        # For development purposes, we'll just display it
        flash(f'OTP for verification: {otp_value}', 'info')
        
        # Simulate sending OTP (in production, use Twilio or similar service)
        send_otp(phone, otp_value)
        
        # Store user ID in session for OTP verification
        session['user_id'] = user.id
        
        return redirect(url_for('verify_otp'))
    
    return render_template('login.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        user_id = session['user_id']
        
        # Find the latest OTP record for the user
        otp_record = OTP.query.filter_by(user_id=user_id).order_by(OTP.created_at.desc()).first()
        
        if not otp_record:
            flash('No OTP record found. Please try again.', 'danger')
            return redirect(url_for('login'))
        
        if submitted_otp == otp_record.otp:
            # OTP verified, mark user as authenticated
            session['authenticated'] = True
            return redirect(url_for('cattle_select'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('verify_otp.html')

@app.route('/cattle-select', methods=['GET', 'POST'])
def cattle_select():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        animal_type = request.form.get('animal_type')
        cattle_type = request.form.get('cattle_type')
        
        if not cattle_type:
            flash('Please select a breed', 'danger')
            return render_template('cattle_select.html')
        
        # Store cattle type and animal type in session
        session['animal_type'] = animal_type
        session['cattle_type'] = cattle_type
        
        return redirect(url_for('health_data'))
    
    return render_template('cattle_select.html')

@app.route('/health-data', methods=['GET', 'POST'])
def health_data():
    if not session.get('authenticated') or 'cattle_type' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        age = request.form.get('age')
        weight = request.form.get('weight')
        heart_rate = request.form.get('heart_rate')
        temperature = request.form.get('temperature')
        milk_yield = request.form.get('milk_yield')
        
        # Get symptoms from form
        symptoms = []
        for key in request.form:
            if key.startswith('symptom_'):
                symptoms.append(request.form[key])
        
        # Additional symptoms from text input
        other_symptoms = request.form.get('other_symptoms', '')
        if other_symptoms:
            symptoms.extend([s.strip() for s in other_symptoms.split(',')])
        
        if not symptoms:
            flash('Please select at least one symptom', 'danger')
            return render_template('health_data.html', cattle_type=session['cattle_type'])
        
        # Handle photo upload if provided
        photo_filename = None
        if 'cattle_photo' in request.files:
            photo = request.files['cattle_photo']
            if photo.filename != '':
                # Generate a unique filename to avoid collisions
                # You could use more sophisticated methods to generate unique filenames
                filename = f"{session.get('user_id')}_{int(time.time())}_{photo.filename}"
                photo_path = os.path.join('static', 'uploads', filename)
                photo.save(photo_path)
                photo_filename = filename
        
        # Save cattle data
        user_id = session['user_id']
        cattle = Cattle(
            user_id=user_id,
            animal_type=session.get('animal_type'),
            cattle_type=session['cattle_type'],
            age=age,
            weight=weight,
            heart_rate=heart_rate,
            temperature=temperature,
            milk_yield=milk_yield,
            symptoms=','.join(symptoms),
            photo_filename=photo_filename
        )
        db.session.add(cattle)
        db.session.commit()
        
        # Store cattle ID in session
        session['cattle_id'] = cattle.id
        
        # Predict disease based on symptoms
        predicted_disease = predict_disease(symptoms)
        session['predicted_disease'] = predicted_disease
        
        # Find nearby vets
        nearby_vets = find_nearby_vets()
        session['nearby_vets'] = [vet.id for vet in nearby_vets]
        
        return redirect(url_for('result'))
    
    return render_template('health_data.html', cattle_type=session['cattle_type'])

@app.route('/result')
def result():
    if not session.get('authenticated') or 'cattle_id' not in session:
        return redirect(url_for('login'))
    
    cattle_id = session['cattle_id']
    cattle = Cattle.query.get(cattle_id)
    
    if not cattle:
        flash('Cattle record not found', 'danger')
        return redirect(url_for('health_data'))
    
    # Get predicted disease
    disease_name = session.get('predicted_disease')
    disease = CattleDisease.query.filter_by(name=disease_name).first()
    
    # Get nearby vets
    vet_ids = session.get('nearby_vets', [])
    nearby_vets = Veterinarian.query.filter(Veterinarian.id.in_(vet_ids)).all()
    
    return render_template('result.html', 
                          cattle=cattle, 
                          disease=disease, 
                          nearby_vets=nearby_vets)

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error="Server error occurred"), 500

import os
import logging
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


if not os.environ.get("TWILIO_ACCOUNT_SID"):
    os.environ["TWILIO_ACCOUNT_SID"] = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_AUTH_TOKEN"):
    os.environ["TWILIO_AUTH_TOKEN"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_PHONE_NUMBER"):
    os.environ["TWILIO_PHONE_NUMBER"] = "+10000000000"                    

from database import db, init_db
from models import User, Cattle, OTP, Veterinarian, CattleDisease
from otp_utils import generate_otp, send_otp
from disease_predictor import predict_disease
from vet_finder import find_nearby_vets

try:
    
    logger.info("Initializing database...")
    init_db(app)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name or not phone:
            flash('Please provide both name and phone number', 'danger')
            return render_template('login.html')
        
        if not phone.isdigit() or len(phone) != 10:
            flash('Please provide a valid 10-digit phone number', 'danger')
            return render_template('login.html')
        
        # Check if user exists, create if not
        user = User.query.filter_by(phone=phone).first()
        if not user:
            user = User(name=name, phone=phone)
            db.session.add(user)
            db.session.commit()
        
        # Generate and save OTP
        otp_value = generate_otp()
        otp_record = OTP(user_id=user.id, otp=otp_value)
        db.session.add(otp_record)
        db.session.commit()
        
        # In a real application, we would send the OTP via SMS
        # For development purposes, we'll just display it
        flash(f'OTP for verification: {otp_value}', 'info')
        
        # Simulate sending OTP (in production, use Twilio or similar service)
        send_otp(phone, otp_value)
        
        # Store user ID in session for OTP verification
        session['user_id'] = user.id
        
        return redirect(url_for('verify_otp'))
    
    return render_template('login.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        user_id = session['user_id']
        
        # Find the latest OTP record for the user
        otp_record = OTP.query.filter_by(user_id=user_id).order_by(OTP.created_at.desc()).first()
        
        if not otp_record:
            flash('No OTP record found. Please try again.', 'danger')
            return redirect(url_for('login'))
        
        if submitted_otp == otp_record.otp:
            # OTP verified, mark user as authenticated
            session['authenticated'] = True
            return redirect(url_for('cattle_select'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('verify_otp.html')

@app.route('/cattle-select', methods=['GET', 'POST'])
def cattle_select():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        animal_type = request.form.get('animal_type')
        cattle_type = request.form.get('cattle_type')
        
        if not cattle_type:
            flash('Please select a breed', 'danger')
            return render_template('cattle_select.html')
        
        # Store cattle type and animal type in session
        session['animal_type'] = animal_type
        session['cattle_type'] = cattle_type
        
        return redirect(url_for('health_data'))
    
    return render_template('cattle_select.html')

@app.route('/health-data', methods=['GET', 'POST'])
def health_data():
    if not session.get('authenticated') or 'cattle_type' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        age = request.form.get('age')
        weight = request.form.get('weight')
        heart_rate = request.form.get('heart_rate')
        temperature = request.form.get('temperature')
        milk_yield = request.form.get('milk_yield')
        
        # Get symptoms from form
        symptoms = []
        for key in request.form:
            if key.startswith('symptom_'):
                symptoms.append(request.form[key])
        
        # Additional symptoms from text input
        other_symptoms = request.form.get('other_symptoms', '')
        if other_symptoms:
            symptoms.extend([s.strip() for s in other_symptoms.split(',')])
        
        if not symptoms:
            flash('Please select at least one symptom', 'danger')
            return render_template('health_data.html', cattle_type=session['cattle_type'])
        
        # Handle photo upload if provided
        photo_filename = None
        if 'cattle_photo' in request.files:
            photo = request.files['cattle_photo']
            if photo.filename != '':
                # Generate a unique filename to avoid collisions
                # You could use more sophisticated methods to generate unique filenames
                filename = f"{session.get('user_id')}_{int(time.time())}_{photo.filename}"
                photo_path = os.path.join('static', 'uploads', filename)
                photo.save(photo_path)
                photo_filename = filename
        
        # Save cattle data
        user_id = session['user_id']
        cattle = Cattle(
            user_id=user_id,
            animal_type=session.get('animal_type'),
            cattle_type=session['cattle_type'],
            age=age,
            weight=weight,
            heart_rate=heart_rate,
            temperature=temperature,
            milk_yield=milk_yield,
            symptoms=','.join(symptoms),
            photo_filename=photo_filename
        )
        db.session.add(cattle)
        db.session.commit()
        
        # Store cattle ID in session
        session['cattle_id'] = cattle.id
        
        # Predict disease based on symptoms
        predicted_disease = predict_disease(symptoms)
        session['predicted_disease'] = predicted_disease
        
        # Find nearby vets
        nearby_vets = find_nearby_vets()
        session['nearby_vets'] = [vet.id for vet in nearby_vets]
        
        return redirect(url_for('result'))
    
    return render_template('health_data.html', cattle_type=session['cattle_type'])

@app.route('/result')
def result():
    if not session.get('authenticated') or 'cattle_id' not in session:
        return redirect(url_for('login'))
    
    cattle_id = session['cattle_id']
    cattle = Cattle.query.get(cattle_id)
    
    if not cattle:
        flash('Cattle record not found', 'danger')
        return redirect(url_for('health_data'))
    
    # Get predicted disease
    disease_name = session.get('predicted_disease')
    disease = CattleDisease.query.filter_by(name=disease_name).first()
    
    # Get nearby vets
    vet_ids = session.get('nearby_vets', [])
    nearby_vets = Veterinarian.query.filter(Veterinarian.id.in_(vet_ids)).all()
    
    return render_template('result.html', 
                          cattle=cattle, 
                          disease=disease, 
                          nearby_vets=nearby_vets)

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error="Server error occurred"), 500

import os
import logging
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


if not os.environ.get("TWILIO_ACCOUNT_SID"):
    os.environ["TWILIO_ACCOUNT_SID"] = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_AUTH_TOKEN"):
    os.environ["TWILIO_AUTH_TOKEN"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_PHONE_NUMBER"):
    os.environ["TWILIO_PHONE_NUMBER"] = "+10000000000"                    

from database import db, init_db
from models import User, Cattle, OTP, Veterinarian, CattleDisease
from otp_utils import generate_otp, send_otp
from disease_predictor import predict_disease
from vet_finder import find_nearby_vets

try:
    
    logger.info("Initializing database...")
    init_db(app)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name or not phone:
            flash('Please provide both name and phone number', 'danger')
            return render_template('login.html')
        
        if not phone.isdigit() or len(phone) != 10:
            flash('Please provide a valid 10-digit phone number', 'danger')
            return render_template('login.html')
        
        # Check if user exists, create if not
        user = User.query.filter_by(phone=phone).first()
        if not user:
            user = User(name=name, phone=phone)
            db.session.add(user)
            db.session.commit()
        
        # Generate and save OTP
        otp_value = generate_otp()
        otp_record = OTP(user_id=user.id, otp=otp_value)
        db.session.add(otp_record)
        db.session.commit()
        
        # In a real application, we would send the OTP via SMS
        # For development purposes, we'll just display it
        flash(f'OTP for verification: {otp_value}', 'info')
        
        # Simulate sending OTP (in production, use Twilio or similar service)
        send_otp(phone, otp_value)
        
        # Store user ID in session for OTP verification
        session['user_id'] = user.id
        
        return redirect(url_for('verify_otp'))
    
    return render_template('login.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        user_id = session['user_id']
        
        # Find the latest OTP record for the user
        otp_record = OTP.query.filter_by(user_id=user_id).order_by(OTP.created_at.desc()).first()
        
        if not otp_record:
            flash('No OTP record found. Please try again.', 'danger')
            return redirect(url_for('login'))
        
        if submitted_otp == otp_record.otp:
            # OTP verified, mark user as authenticated
            session['authenticated'] = True
            return redirect(url_for('cattle_select'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('verify_otp.html')

@app.route('/cattle-select', methods=['GET', 'POST'])
def cattle_select():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        animal_type = request.form.get('animal_type')
        cattle_type = request.form.get('cattle_type')
        
        if not cattle_type:
            flash('Please select a breed', 'danger')
            return render_template('cattle_select.html')
        
        # Store cattle type and animal type in session
        session['animal_type'] = animal_type
        session['cattle_type'] = cattle_type
        
        return redirect(url_for('health_data'))
    
    return render_template('cattle_select.html')

@app.route('/health-data', methods=['GET', 'POST'])
def health_data():
    if not session.get('authenticated') or 'cattle_type' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        age = request.form.get('age')
        weight = request.form.get('weight')
        heart_rate = request.form.get('heart_rate')
        temperature = request.form.get('temperature')
        milk_yield = request.form.get('milk_yield')
        
        # Get symptoms from form
        symptoms = []
        for key in request.form:
            if key.startswith('symptom_'):
                symptoms.append(request.form[key])
        
        # Additional symptoms from text input
        other_symptoms = request.form.get('other_symptoms', '')
        if other_symptoms:
            symptoms.extend([s.strip() for s in other_symptoms.split(',')])
        
        if not symptoms:
            flash('Please select at least one symptom', 'danger')
            return render_template('health_data.html', cattle_type=session['cattle_type'])
        
        # Handle photo upload if provided
        photo_filename = None
        if 'cattle_photo' in request.files:
            photo = request.files['cattle_photo']
            if photo.filename != '':
                # Generate a unique filename to avoid collisions
                # You could use more sophisticated methods to generate unique filenames
                filename = f"{session.get('user_id')}_{int(time.time())}_{photo.filename}"
                photo_path = os.path.join('static', 'uploads', filename)
                photo.save(photo_path)
                photo_filename = filename
        
        # Save cattle data
        user_id = session['user_id']
        cattle = Cattle(
            user_id=user_id,
            animal_type=session.get('animal_type'),
            cattle_type=session['cattle_type'],
            age=age,
            weight=weight,
            heart_rate=heart_rate,
            temperature=temperature,
            milk_yield=milk_yield,
            symptoms=','.join(symptoms),
            photo_filename=photo_filename
        )
        db.session.add(cattle)
        db.session.commit()
        
        # Store cattle ID in session
        session['cattle_id'] = cattle.id
        
        # Predict disease based on symptoms
        predicted_disease = predict_disease(symptoms)
        session['predicted_disease'] = predicted_disease
        
        # Find nearby vets
        nearby_vets = find_nearby_vets()
        session['nearby_vets'] = [vet.id for vet in nearby_vets]
        
        return redirect(url_for('result'))
    
    return render_template('health_data.html', cattle_type=session['cattle_type'])

@app.route('/result')
def result():
    if not session.get('authenticated') or 'cattle_id' not in session:
        return redirect(url_for('login'))
    
    cattle_id = session['cattle_id']
    cattle = Cattle.query.get(cattle_id)
    
    if not cattle:
        flash('Cattle record not found', 'danger')
        return redirect(url_for('health_data'))
    
    # Get predicted disease
    disease_name = session.get('predicted_disease')
    disease = CattleDisease.query.filter_by(name=disease_name).first()
    
    # Get nearby vets
    vet_ids = session.get('nearby_vets', [])
    nearby_vets = Veterinarian.query.filter(Veterinarian.id.in_(vet_ids)).all()
    
    return render_template('result.html', 
                          cattle=cattle, 
                          disease=disease, 
                          nearby_vets=nearby_vets)

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error="Server error occurred"), 500

import os
import logging
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


if not os.environ.get("TWILIO_ACCOUNT_SID"):
    os.environ["TWILIO_ACCOUNT_SID"] = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_AUTH_TOKEN"):
    os.environ["TWILIO_AUTH_TOKEN"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_PHONE_NUMBER"):
    os.environ["TWILIO_PHONE_NUMBER"] = "+10000000000"                    

from database import db, init_db
from models import User, Cattle, OTP, Veterinarian, CattleDisease
from otp_utils import generate_otp, send_otp
from disease_predictor import predict_disease
from vet_finder import find_nearby_vets

try:
    
    logger.info("Initializing database...")
    init_db(app)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name or not phone:
            flash('Please provide both name and phone number', 'danger')
            return render_template('login.html')
        
        if not phone.isdigit() or len(phone) != 10:
            flash('Please provide a valid 10-digit phone number', 'danger')
            return render_template('login.html')
        
        # Check if user exists, create if not
        user = User.query.filter_by(phone=phone).first()
        if not user:
            user = User(name=name, phone=phone)
            db.session.add(user)
            db.session.commit()
        
        # Generate and save OTP
        otp_value = generate_otp()
        otp_record = OTP(user_id=user.id, otp=otp_value)
        db.session.add(otp_record)
        db.session.commit()
        
        # In a real application, we would send the OTP via SMS
        # For development purposes, we'll just display it
        flash(f'OTP for verification: {otp_value}', 'info')
        
        # Simulate sending OTP (in production, use Twilio or similar service)
        send_otp(phone, otp_value)
        
        # Store user ID in session for OTP verification
        session['user_id'] = user.id
        
        return redirect(url_for('verify_otp'))
    
    return render_template('login.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        user_id = session['user_id']
        
        # Find the latest OTP record for the user
        otp_record = OTP.query.filter_by(user_id=user_id).order_by(OTP.created_at.desc()).first()
        
        if not otp_record:
            flash('No OTP record found. Please try again.', 'danger')
            return redirect(url_for('login'))
        
        if submitted_otp == otp_record.otp:
            # OTP verified, mark user as authenticated
            session['authenticated'] = True
            return redirect(url_for('cattle_select'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('verify_otp.html')

@app.route('/cattle-select', methods=['GET', 'POST'])
def cattle_select():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        animal_type = request.form.get('animal_type')
        cattle_type = request.form.get('cattle_type')
        
        if not cattle_type:
            flash('Please select a breed', 'danger')
            return render_template('cattle_select.html')
        
        # Store cattle type and animal type in session
        session['animal_type'] = animal_type
        session['cattle_type'] = cattle_type
        
        return redirect(url_for('health_data'))
    
    return render_template('cattle_select.html')

@app.route('/health-data', methods=['GET', 'POST'])
def health_data():
    if not session.get('authenticated') or 'cattle_type' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        age = request.form.get('age')
        weight = request.form.get('weight')
        heart_rate = request.form.get('heart_rate')
        temperature = request.form.get('temperature')
        milk_yield = request.form.get('milk_yield')
        
        # Get symptoms from form
        symptoms = []
        for key in request.form:
            if key.startswith('symptom_'):
                symptoms.append(request.form[key])
        
        # Additional symptoms from text input
        other_symptoms = request.form.get('other_symptoms', '')
        if other_symptoms:
            symptoms.extend([s.strip() for s in other_symptoms.split(',')])
        
        if not symptoms:
            flash('Please select at least one symptom', 'danger')
            return render_template('health_data.html', cattle_type=session['cattle_type'])
        
        # Handle photo upload if provided
        photo_filename = None
        if 'cattle_photo' in request.files:
            photo = request.files['cattle_photo']
            if photo.filename != '':
                # Generate a unique filename to avoid collisions
                # You could use more sophisticated methods to generate unique filenames
                filename = f"{session.get('user_id')}_{int(time.time())}_{photo.filename}"
                photo_path = os.path.join('static', 'uploads', filename)
                photo.save(photo_path)
                photo_filename = filename
        
        # Save cattle data
        user_id = session['user_id']
        cattle = Cattle(
            user_id=user_id,
            animal_type=session.get('animal_type'),
            cattle_type=session['cattle_type'],
            age=age,
            weight=weight,
            heart_rate=heart_rate,
            temperature=temperature,
            milk_yield=milk_yield,
            symptoms=','.join(symptoms),
            photo_filename=photo_filename
        )
        db.session.add(cattle)
        db.session.commit()
        
        # Store cattle ID in session
        session['cattle_id'] = cattle.id
        
        # Predict disease based on symptoms
        predicted_disease = predict_disease(symptoms)
        session['predicted_disease'] = predicted_disease
        
        # Find nearby vets
        nearby_vets = find_nearby_vets()
        session['nearby_vets'] = [vet.id for vet in nearby_vets]
        
        return redirect(url_for('result'))
    
    return render_template('health_data.html', cattle_type=session['cattle_type'])

@app.route('/result')
def result():
    if not session.get('authenticated') or 'cattle_id' not in session:
        return redirect(url_for('login'))
    
    cattle_id = session['cattle_id']
    cattle = Cattle.query.get(cattle_id)
    
    if not cattle:
        flash('Cattle record not found', 'danger')
        return redirect(url_for('health_data'))
    
    # Get predicted disease
    disease_name = session.get('predicted_disease')
    disease = CattleDisease.query.filter_by(name=disease_name).first()
    
    # Get nearby vets
    vet_ids = session.get('nearby_vets', [])
    nearby_vets = Veterinarian.query.filter(Veterinarian.id.in_(vet_ids)).all()
    
    return render_template('result.html', 
                          cattle=cattle, 
                          disease=disease, 
                          nearby_vets=nearby_vets)

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error="Server error occurred"), 500

import os
import logging
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


if not os.environ.get("TWILIO_ACCOUNT_SID"):
    os.environ["TWILIO_ACCOUNT_SID"] = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_AUTH_TOKEN"):
    os.environ["TWILIO_AUTH_TOKEN"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_PHONE_NUMBER"):
    os.environ["TWILIO_PHONE_NUMBER"] = "+10000000000"                    

from database import db, init_db
from models import User, Cattle, OTP, Veterinarian, CattleDisease
from otp_utils import generate_otp, send_otp
from disease_predictor import predict_disease
from vet_finder import find_nearby_vets

try:
    
    logger.info("Initializing database...")
    init_db(app)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name or not phone:
            flash('Please provide both name and phone number', 'danger')
            return render_template('login.html')
        
        if not phone.isdigit() or len(phone) != 10:
            flash('Please provide a valid 10-digit phone number', 'danger')
            return render_template('login.html')
        
        # Check if user exists, create if not
        user = User.query.filter_by(phone=phone).first()
        if not user:
            user = User(name=name, phone=phone)
            db.session.add(user)
            db.session.commit()
        
        # Generate and save OTP
        otp_value = generate_otp()
        otp_record = OTP(user_id=user.id, otp=otp_value)
        db.session.add(otp_record)
        db.session.commit()
        
        # In a real application, we would send the OTP via SMS
        # For development purposes, we'll just display it
        flash(f'OTP for verification: {otp_value}', 'info')
        
        # Simulate sending OTP (in production, use Twilio or similar service)
        send_otp(phone, otp_value)
        
        # Store user ID in session for OTP verification
        session['user_id'] = user.id
        
        return redirect(url_for('verify_otp'))
    
    return render_template('login.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        user_id = session['user_id']
        
        # Find the latest OTP record for the user
        otp_record = OTP.query.filter_by(user_id=user_id).order_by(OTP.created_at.desc()).first()
        
        if not otp_record:
            flash('No OTP record found. Please try again.', 'danger')
            return redirect(url_for('login'))
        
        if submitted_otp == otp_record.otp:
            # OTP verified, mark user as authenticated
            session['authenticated'] = True
            return redirect(url_for('cattle_select'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('verify_otp.html')

@app.route('/cattle-select', methods=['GET', 'POST'])
def cattle_select():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        animal_type = request.form.get('animal_type')
        cattle_type = request.form.get('cattle_type')
        
        if not cattle_type:
            flash('Please select a breed', 'danger')
            return render_template('cattle_select.html')
        
        # Store cattle type and animal type in session
        session['animal_type'] = animal_type
        session['cattle_type'] = cattle_type
        
        return redirect(url_for('health_data'))
    
    return render_template('cattle_select.html')

@app.route('/health-data', methods=['GET', 'POST'])
def health_data():
    if not session.get('authenticated') or 'cattle_type' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        age = request.form.get('age')
        weight = request.form.get('weight')
        heart_rate = request.form.get('heart_rate')
        temperature = request.form.get('temperature')
        milk_yield = request.form.get('milk_yield')
        
        # Get symptoms from form
        symptoms = []
        for key in request.form:
            if key.startswith('symptom_'):
                symptoms.append(request.form[key])
        
        # Additional symptoms from text input
        other_symptoms = request.form.get('other_symptoms', '')
        if other_symptoms:
            symptoms.extend([s.strip() for s in other_symptoms.split(',')])
        
        if not symptoms:
            flash('Please select at least one symptom', 'danger')
            return render_template('health_data.html', cattle_type=session['cattle_type'])
        
        # Handle photo upload if provided
        photo_filename = None
        if 'cattle_photo' in request.files:
            photo = request.files['cattle_photo']
            if photo.filename != '':
                # Generate a unique filename to avoid collisions
                # You could use more sophisticated methods to generate unique filenames
                filename = f"{session.get('user_id')}_{int(time.time())}_{photo.filename}"
                photo_path = os.path.join('static', 'uploads', filename)
                photo.save(photo_path)
                photo_filename = filename
        
        # Save cattle data
        user_id = session['user_id']
        cattle = Cattle(
            user_id=user_id,
            animal_type=session.get('animal_type'),
            cattle_type=session['cattle_type'],
            age=age,
            weight=weight,
            heart_rate=heart_rate,
            temperature=temperature,
            milk_yield=milk_yield,
            symptoms=','.join(symptoms),
            photo_filename=photo_filename
        )
        db.session.add(cattle)
        db.session.commit()
        
        # Store cattle ID in session
        session['cattle_id'] = cattle.id
        
        # Predict disease based on symptoms
        predicted_disease = predict_disease(symptoms)
        session['predicted_disease'] = predicted_disease
        
        # Find nearby vets
        nearby_vets = find_nearby_vets()
        session['nearby_vets'] = [vet.id for vet in nearby_vets]
        
        return redirect(url_for('result'))
    
    return render_template('health_data.html', cattle_type=session['cattle_type'])

@app.route('/result')
def result():
    if not session.get('authenticated') or 'cattle_id' not in session:
        return redirect(url_for('login'))
    
    cattle_id = session['cattle_id']
    cattle = Cattle.query.get(cattle_id)
    
    if not cattle:
        flash('Cattle record not found', 'danger')
        return redirect(url_for('health_data'))
    
    # Get predicted disease
    disease_name = session.get('predicted_disease')
    disease = CattleDisease.query.filter_by(name=disease_name).first()
    
    # Get nearby vets
    vet_ids = session.get('nearby_vets', [])
    nearby_vets = Veterinarian.query.filter(Veterinarian.id.in_(vet_ids)).all()
    
    return render_template('result.html', 
                          cattle=cattle, 
                          disease=disease, 
                          nearby_vets=nearby_vets)

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error="Server error occurred"), 500

import os
import logging
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


if not os.environ.get("TWILIO_ACCOUNT_SID"):
    os.environ["TWILIO_ACCOUNT_SID"] = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_AUTH_TOKEN"):
    os.environ["TWILIO_AUTH_TOKEN"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_PHONE_NUMBER"):
    os.environ["TWILIO_PHONE_NUMBER"] = "+10000000000"                    

from database import db, init_db
from models import User, Cattle, OTP, Veterinarian, CattleDisease
from otp_utils import generate_otp, send_otp
from disease_predictor import predict_disease
from vet_finder import find_nearby_vets

try:
    
    logger.info("Initializing database...")
    init_db(app)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name or not phone:
            flash('Please provide both name and phone number', 'danger')
            return render_template('login.html')
        
        if not phone.isdigit() or len(phone) != 10:
            flash('Please provide a valid 10-digit phone number', 'danger')
            return render_template('login.html')
        
        # Check if user exists, create if not
        user = User.query.filter_by(phone=phone).first()
        if not user:
            user = User(name=name, phone=phone)
            db.session.add(user)
            db.session.commit()
        
        # Generate and save OTP
        otp_value = generate_otp()
        otp_record = OTP(user_id=user.id, otp=otp_value)
        db.session.add(otp_record)
        db.session.commit()
        
        # In a real application, we would send the OTP via SMS
        # For development purposes, we'll just display it
        flash(f'OTP for verification: {otp_value}', 'info')
        
        # Simulate sending OTP (in production, use Twilio or similar service)
        send_otp(phone, otp_value)
        
        # Store user ID in session for OTP verification
        session['user_id'] = user.id
        
        return redirect(url_for('verify_otp'))
    
    return render_template('login.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        user_id = session['user_id']
        
        # Find the latest OTP record for the user
        otp_record = OTP.query.filter_by(user_id=user_id).order_by(OTP.created_at.desc()).first()
        
        if not otp_record:
            flash('No OTP record found. Please try again.', 'danger')
            return redirect(url_for('login'))
        
        if submitted_otp == otp_record.otp:
            # OTP verified, mark user as authenticated
            session['authenticated'] = True
            return redirect(url_for('cattle_select'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('verify_otp.html')

@app.route('/cattle-select', methods=['GET', 'POST'])
def cattle_select():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        animal_type = request.form.get('animal_type')
        cattle_type = request.form.get('cattle_type')
        
        if not cattle_type:
            flash('Please select a breed', 'danger')
            return render_template('cattle_select.html')
        
        # Store cattle type and animal type in session
        session['animal_type'] = animal_type
        session['cattle_type'] = cattle_type
        
        return redirect(url_for('health_data'))
    
    return render_template('cattle_select.html')

@app.route('/health-data', methods=['GET', 'POST'])
def health_data():
    if not session.get('authenticated') or 'cattle_type' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        age = request.form.get('age')
        weight = request.form.get('weight')
        heart_rate = request.form.get('heart_rate')
        temperature = request.form.get('temperature')
        milk_yield = request.form.get('milk_yield')
        
        # Get symptoms from form
        symptoms = []
        for key in request.form:
            if key.startswith('symptom_'):
                symptoms.append(request.form[key])
        
        # Additional symptoms from text input
        other_symptoms = request.form.get('other_symptoms', '')
        if other_symptoms:
            symptoms.extend([s.strip() for s in other_symptoms.split(',')])
        
        if not symptoms:
            flash('Please select at least one symptom', 'danger')
            return render_template('health_data.html', cattle_type=session['cattle_type'])
        
        # Handle photo upload if provided
        photo_filename = None
        if 'cattle_photo' in request.files:
            photo = request.files['cattle_photo']
            if photo.filename != '':
                # Generate a unique filename to avoid collisions
                # You could use more sophisticated methods to generate unique filenames
                filename = f"{session.get('user_id')}_{int(time.time())}_{photo.filename}"
                photo_path = os.path.join('static', 'uploads', filename)
                photo.save(photo_path)
                photo_filename = filename
        
        # Save cattle data
        user_id = session['user_id']
        cattle = Cattle(
            user_id=user_id,
            animal_type=session.get('animal_type'),
            cattle_type=session['cattle_type'],
            age=age,
            weight=weight,
            heart_rate=heart_rate,
            temperature=temperature,
            milk_yield=milk_yield,
            symptoms=','.join(symptoms),
            photo_filename=photo_filename
        )
        db.session.add(cattle)
        db.session.commit()
        
        # Store cattle ID in session
        session['cattle_id'] = cattle.id
        
        # Predict disease based on symptoms
        predicted_disease = predict_disease(symptoms)
        session['predicted_disease'] = predicted_disease
        
        # Find nearby vets
        nearby_vets = find_nearby_vets()
        session['nearby_vets'] = [vet.id for vet in nearby_vets]
        
        return redirect(url_for('result'))
    
    return render_template('health_data.html', cattle_type=session['cattle_type'])

@app.route('/result')
def result():
    if not session.get('authenticated') or 'cattle_id' not in session:
        return redirect(url_for('login'))
    
    cattle_id = session['cattle_id']
    cattle = Cattle.query.get(cattle_id)
    
    if not cattle:
        flash('Cattle record not found', 'danger')
        return redirect(url_for('health_data'))
    
    # Get predicted disease
    disease_name = session.get('predicted_disease')
    disease = CattleDisease.query.filter_by(name=disease_name).first()
    
    # Get nearby vets
    vet_ids = session.get('nearby_vets', [])
    nearby_vets = Veterinarian.query.filter(Veterinarian.id.in_(vet_ids)).all()
    
    return render_template('result.html', 
                          cattle=cattle, 
                          disease=disease, 
                          nearby_vets=nearby_vets)

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error="Server error occurred"), 500

import os
import logging
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


if not os.environ.get("TWILIO_ACCOUNT_SID"):
    os.environ["TWILIO_ACCOUNT_SID"] = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_AUTH_TOKEN"):
    os.environ["TWILIO_AUTH_TOKEN"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_PHONE_NUMBER"):
    os.environ["TWILIO_PHONE_NUMBER"] = "+10000000000"                    

from database import db, init_db
from models import User, Cattle, OTP, Veterinarian, CattleDisease
from otp_utils import generate_otp, send_otp
from disease_predictor import predict_disease
from vet_finder import find_nearby_vets

try:
    
    logger.info("Initializing database...")
    init_db(app)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name or not phone:
            flash('Please provide both name and phone number', 'danger')
            return render_template('login.html')
        
        if not phone.isdigit() or len(phone) != 10:
            flash('Please provide a valid 10-digit phone number', 'danger')
            return render_template('login.html')
        
        # Check if user exists, create if not
        user = User.query.filter_by(phone=phone).first()
        if not user:
            user = User(name=name, phone=phone)
            db.session.add(user)
            db.session.commit()
        
        # Generate and save OTP
        otp_value = generate_otp()
        otp_record = OTP(user_id=user.id, otp=otp_value)
        db.session.add(otp_record)
        db.session.commit()
        
        # In a real application, we would send the OTP via SMS
        # For development purposes, we'll just display it
        flash(f'OTP for verification: {otp_value}', 'info')
        
        # Simulate sending OTP (in production, use Twilio or similar service)
        send_otp(phone, otp_value)
        
        # Store user ID in session for OTP verification
        session['user_id'] = user.id
        
        return redirect(url_for('verify_otp'))
    
    return render_template('login.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        user_id = session['user_id']
        
        # Find the latest OTP record for the user
        otp_record = OTP.query.filter_by(user_id=user_id).order_by(OTP.created_at.desc()).first()
        
        if not otp_record:
            flash('No OTP record found. Please try again.', 'danger')
            return redirect(url_for('login'))
        
        if submitted_otp == otp_record.otp:
            # OTP verified, mark user as authenticated
            session['authenticated'] = True
            return redirect(url_for('cattle_select'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('verify_otp.html')

@app.route('/cattle-select', methods=['GET', 'POST'])
def cattle_select():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        animal_type = request.form.get('animal_type')
        cattle_type = request.form.get('cattle_type')
        
        if not cattle_type:
            flash('Please select a breed', 'danger')
            return render_template('cattle_select.html')
        
        # Store cattle type and animal type in session
        session['animal_type'] = animal_type
        session['cattle_type'] = cattle_type
        
        return redirect(url_for('health_data'))
    
    return render_template('cattle_select.html')

@app.route('/health-data', methods=['GET', 'POST'])
def health_data():
    if not session.get('authenticated') or 'cattle_type' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        age = request.form.get('age')
        weight = request.form.get('weight')
        heart_rate = request.form.get('heart_rate')
        temperature = request.form.get('temperature')
        milk_yield = request.form.get('milk_yield')
        
        # Get symptoms from form
        symptoms = []
        for key in request.form:
            if key.startswith('symptom_'):
                symptoms.append(request.form[key])
        
        # Additional symptoms from text input
        other_symptoms = request.form.get('other_symptoms', '')
        if other_symptoms:
            symptoms.extend([s.strip() for s in other_symptoms.split(',')])
        
        if not symptoms:
            flash('Please select at least one symptom', 'danger')
            return render_template('health_data.html', cattle_type=session['cattle_type'])
        
        # Handle photo upload if provided
        photo_filename = None
        if 'cattle_photo' in request.files:
            photo = request.files['cattle_photo']
            if photo.filename != '':
                # Generate a unique filename to avoid collisions
                # You could use more sophisticated methods to generate unique filenames
                filename = f"{session.get('user_id')}_{int(time.time())}_{photo.filename}"
                photo_path = os.path.join('static', 'uploads', filename)
                photo.save(photo_path)
                photo_filename = filename
        
        # Save cattle data
        user_id = session['user_id']
        cattle = Cattle(
            user_id=user_id,
            animal_type=session.get('animal_type'),
            cattle_type=session['cattle_type'],
            age=age,
            weight=weight,
            heart_rate=heart_rate,
            temperature=temperature,
            milk_yield=milk_yield,
            symptoms=','.join(symptoms),
            photo_filename=photo_filename
        )
        db.session.add(cattle)
        db.session.commit()
        
        # Store cattle ID in session
        session['cattle_id'] = cattle.id
        
        # Predict disease based on symptoms
        predicted_disease = predict_disease(symptoms)
        session['predicted_disease'] = predicted_disease
        
        # Find nearby vets
        nearby_vets = find_nearby_vets()
        session['nearby_vets'] = [vet.id for vet in nearby_vets]
        
        return redirect(url_for('result'))
    
    return render_template('health_data.html', cattle_type=session['cattle_type'])

@app.route('/result')
def result():
    if not session.get('authenticated') or 'cattle_id' not in session:
        return redirect(url_for('login'))
    
    cattle_id = session['cattle_id']
    cattle = Cattle.query.get(cattle_id)
    
    if not cattle:
        flash('Cattle record not found', 'danger')
        return redirect(url_for('health_data'))
    
    # Get predicted disease
    disease_name = session.get('predicted_disease')
    disease = CattleDisease.query.filter_by(name=disease_name).first()
    
    # Get nearby vets
    vet_ids = session.get('nearby_vets', [])
    nearby_vets = Veterinarian.query.filter(Veterinarian.id.in_(vet_ids)).all()
    
    return render_template('result.html', 
                          cattle=cattle, 
                          disease=disease, 
                          nearby_vets=nearby_vets)

@app.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error="Server error occurred"), 500

import os
import logging
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


if not os.environ.get("TWILIO_ACCOUNT_SID"):
    os.environ["TWILIO_ACCOUNT_SID"] = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_AUTH_TOKEN"):
    os.environ["TWILIO_AUTH_TOKEN"] = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
if not os.environ.get("TWILIO_PHONE_NUMBER"):
    os.environ["TWILIO_PHONE_NUMBER"] = "+10000000000"                    

from database import db, init_db
from models import User, Cattle, OTP, Veterinarian, CattleDisease
from otp_utils import generate_otp, send_otp
from disease_predictor import predict_disease
from vet_finder import find_nearby_vets

try:
    
    logger.info("Initializing database...")
    init_db(app)
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name or not phone:
            flash('Please provide both name and phone number', 'danger')
            return render_template('login.html')
        
        if not phone.isdigit() or len(phone) != 10:
            flash('Please provide a valid 10-digit phone number', 'danger')
            return render_template('login.html')
        
        # Check if user exists, create if not
        user = User.query.filter_by(phone=phone).first()
        if not user:
            user = User(name=name, phone=phone)
            db.session.add(user)
            db.session.commit()
        
        # Generate and save OTP
        otp_value = generate_otp()
        otp_record = OTP(user_id=user.id, otp=otp_value)
        db.session.add(otp_record)
        db.session.commit()
        
        # In a real application, we would send the OTP via SMS
        # For development purposes, we'll just display it
        flash(f'OTP for verification: {otp_value}', 'info')
        
        # Simulate sending OTP (in production, use Twilio or similar service)
        send_otp(phone, otp_value)
        
        # Store user ID in session for OTP verification
        session['user_id'] = user.id
        
        return redirect(url_for('verify_otp'))
    
    return render_template('login.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        submitted_otp = request.form.get('otp')
        user_id = session['user_id']
        
        # Find the latest OTP record for the user
        otp_record = OTP.query.filter_by(user_id=user_id).order_by(OTP.created_at.desc()).first()
        
        if not otp_record:
            flash('No OTP record found. Please try again.', 'danger')
            return redirect(url_for('login'))
        
        if submitted_otp == otp_record.otp:
            # OTP verified, mark user as authenticated
            session['authenticated'] = True
            return redirect(url_for('cattle_select'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('verify_otp.html')

@app.route('/cattle-select', methods=['GET', 'POST'])
def cattle_select():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        animal_type = request.form.get('animal_type')
        cattle_type = request.form.get('cattle_type')
        
        if not cattle_type:
            flash('Please select a breed', 'danger')
            return render_template('cattle_select.html')
        
        # Store cattle type and animal type in session
        session['animal_type'] = animal_type
        session['cattle_type'] = cattle_type
        
        return redirect(url_for('health_data'))
    
    return render_template('cattle_select.html')

@app.route('/health-data', methods=['GET', 'POST'])
def health_data():
    if not session.get('authenticated') or 'cattle_type' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        age = request.form.get('age')
        weight = request.form.get('weight')
        heart_rate = request.form.get('heart_rate')
        temperature = request.form.get('temperature')
        milk_yield = request.form.get('milk_yield')
        
        # Get symptoms from form
        symptoms = []
        for key in request.form:
            if key.startswith('symptom_'):
                symptoms.append(request.form[key])
        
        # Additional symptoms from text input
        other_symptoms = request.form.get('other_symptoms', '')
        if other_symptoms:
            symptoms.extend([s.strip() for s in other_symptoms.split(',')])
        
        if not symptoms:
            flash('Please select at least one symptom', 'danger')
            return render_template('health_data.html', cattle_type=session['cattle_type'])
        
        # Handle photo upload if provided
        photo_filename = None
        if 'cattle_photo' in request.files:
            photo = request.files['cattle_photo']
            if photo.filename != '':
                # Generate a unique filename to avoid collisions
                # You could use more sophisticated methods to generate unique filenames
                filename = f"{session.get('user_id')}_{int(time.time())}_{photo.filename}"
                photo_path = os.path.join('static', 'uploads', filename)
                photo.save(photo_path)
                photo_filename = filename
        
        # Save cattle data
        user_id = session['user_id']
        cattle = Cattle(
            user_id=user_id,
            animal_type=session.get('animal_type'),
            cattle_type=session['cattle_type'],
            age=age,
            weight=weight,
            heart_rate=heart_rate,
            temperature=temperature,
            milk_yield=milk_yield,
            symptoms=','.join(symptoms),
            photo_filename=photo_filename
        )
        db.session.add(cattle)
        db.session.commit()
        
        # Store cattle ID in session
        session['cattle_id'] = cattle.id
        
        # Predict disease based on symptoms
        predicted_disease = predict_disease(symptoms)
        session['predicted_disease'] = predicted_disease
        
        # Find nearby vets
        nearby_vets = find_nearby_vets()
        session['nearby_vets'] = [vet.id for vet in nearby_vets]
        
        return redirect(url_for('result'))
    
    return render_template('health_data.html', cattle_type=session['cattle_type'])

@app.route('/result')
def result():
    if not session.get('authenticated') or 'cattle
