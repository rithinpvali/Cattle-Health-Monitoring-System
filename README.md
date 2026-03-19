🐄 Cattle Health Monitoring System

A smart AI-powered web application that helps farmers monitor their 
cattle's health, predict diseases based on symptoms, and find nearby 
veterinarians — all in one platform.

🚀 Features

- **OTP Authentication** — Secure phone number-based login using OTP via Twilio SMS
- **Cattle Registration** — Register cattle with breed, age, weight, heart rate, temperature, milk yield, and photo
- **AI Disease Prediction** — Predicts cattle diseases based on reported symptoms using a weighted matching algorithm
- **Disease Information** — Displays disease description, severity level, and precautions for each detected condition
- **Nearby Vet Finder** — Finds closest veterinarians using GPS coordinates and the Haversine distance formula
- **Multi-Animal Support** — Supports both Cow/Oxen and Buffalo with breed-specific tracking
- **Photo Upload** — Upload cattle photos for visual health records
- **SQLite Database** — Lightweight local database storing users, cattle, diseases, OTPs, and vet records


🦠 Diseases Covered

| Disease | Severity |
|---------|----------|
| Mastitis | 🔴 High |
| Foot and Mouth Disease | 🔴 High |
| Bovine Respiratory Disease | 🔴 High |
| Bloat | 🟡 Medium |
| Milk Fever | 🟡 Medium |


🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.11 | Backend Language |
| Flask | Web Framework |
| Flask-SQLAlchemy | ORM & Database Management |
| SQLite | Local Database |
| Twilio | OTP SMS Service |
| Gunicorn | Production Server |
| HTML / CSS / JS | Frontend |

 📁 Project Structure

cattle-health-monitor/
├── main.py                 # App entry point
├── app.py                  # Flask app configuration & routes
├── models.py               # Database models (User, Cattle, Disease, Vet, OTP)
├── database.py             # DB initialization & sample data seeding
├── disease_predictor.py    # AI symptom-to-disease matching algorithm
├── vet_finder.py           # Nearby vet finder using Haversine formula
├── otp_utils.py            # OTP generation & Twilio SMS sending
├── populate_diseases.py    # Script to populate disease data
├── init_new_db.py          # Database re-initialization script
├── cattle_health.db        # SQLite database file
├── pyproject.toml          # Project dependencies
└── generated-icon.png      # App icon


 ⚙️ How to Run

 1. Clone the Repository
bash
git clone https://github.com/your-username/cattle-health-monitor.git
cd cattle-health-monitor


 2. Install Dependencies
bash
pip install flask flask-sqlalchemy gunicorn twilio psycopg2-binary


3. Set Environment Variables (Optional for OTP SMS)
bash
export TWILIO_ACCOUNT_SID=your_account_sid
export TWILIO_AUTH_TOKEN=your_auth_token
export TWILIO_PHONE_NUMBER=your_twilio_number
export SESSION_SECRET=your_secret_key


4. Run the App
bash
python main.py


 5. Open in Browser
http://localhost:5000


💡 If Twilio credentials are not set, OTPs will be logged 
in the terminal for development/testing purposes.

 🧠 How Disease Prediction Works

The AI engine in `disease_predictor.py` uses a **weighted symptom 
matching algorithm**:

1. Farmer enters observed symptoms
2. System compares against all diseases in the database
3. Scores each disease based on:
   - ✅ Exact symptom matches (weight: 3x)
   - 🔁 Partial symptom matches (weight: 0.5x)
   - 📊 Symptom coverage ratio
   - ⚠️ Disease severity bias
4. Returns the highest-scoring disease as the prediction

📍 How Vet Finder Works

The `vet_finder.py` module uses the **Haversine Formula** to calculate 
the real-world distance (in km) between the farmer's GPS location and 
each registered veterinarian, then returns the nearest ones.


💡 Real-World Problem Solved

Farmers in rural areas often cannot identify cattle diseases early, 
leading to loss of livestock and income. This system gives farmers 
a smart, easy-to-use tool to monitor cattle health, detect diseases 
early using AI, and quickly connect with the nearest veterinarian — 
saving both animals and livelihoods.

 🙋 Author
    Rithin P.Vali 
