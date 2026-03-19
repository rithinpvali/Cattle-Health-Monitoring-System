import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Create SQLAlchemy instance
db = SQLAlchemy(model_class=Base)

# Create Flask app and configure database
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize app with SQLAlchemy
db.init_app(app)

# Define CattleDisease model directly here to avoid circular imports
class CattleDisease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    symptoms = db.Column(db.Text, nullable=False)  # Comma-separated list of symptoms
    description = db.Column(db.Text, nullable=False)
    precautions = db.Column(db.Text, nullable=False)  # Comma-separated list of precautions
    severity = db.Column(db.String(20), nullable=False)  # Low, Medium, High
    
    def __repr__(self):
        return f'<CattleDisease {self.name}>'

# Function to add a disease to the database
def add_disease(name, symptoms, description, precautions, severity):
    # Check if disease already exists
    existing = CattleDisease.query.filter_by(name=name).first()
    if existing:
        print(f"Disease '{name}' already exists, skipping.")
        return

    # Create new disease record
    disease = CattleDisease(
        name=name,
        symptoms=symptoms,
        description=description,
        precautions=precautions,
        severity=severity
    )
    db.session.add(disease)
    print(f"Added disease: {name}")

# List of cattle diseases with their details
def populate_diseases():
    # Clear existing diseases if --clear flag is provided
    if len(sys.argv) > 1 and sys.argv[1] == '--clear':
        print("Clearing existing diseases...")
        CattleDisease.query.delete()
    
    # Common Bacterial Diseases
    add_disease(
        name="Bovine Respiratory Disease (BRD)",
        symptoms="Fever,Nasal discharge,Coughing,Rapid breathing,Lethargy,Reduced appetite",
        description="A complex of diseases affecting the lower respiratory tract, commonly known as shipping fever. It's one of the most significant health problems in cattle industry worldwide.",
        precautions="Proper ventilation,Vaccination,Stress reduction,Isolation of sick animals,Early treatment with antibiotics",
        severity="High"
    )
    
    add_disease(
        name="Foot Rot",
        symptoms="Lameness,Swelling between toes,Foul smell,Fever,Reduced appetite,Decreased milk production",
        description="A bacterial infection that causes inflammation and necrosis of the tissue between the toes and surrounding areas of the hoof.",
        precautions="Regular hoof care,Clean and dry environment,Footbaths with antibacterial solutions,Prompt treatment of affected animals,Maintaining good drainage in pens",
        severity="Medium"
    )
    
    add_disease(
        name="Mastitis",
        symptoms="Swollen udder,Abnormal milk,Reduced milk production,Fever,Hard udder,Pain during milking",
        description="Inflammation of the mammary gland, usually caused by bacterial infection. One of the most costly diseases in dairy cattle.",
        precautions="Clean milking equipment,Proper milking technique,Teat dipping,Regular udder inspection,Culling chronically infected cows,Proper nutrition",
        severity="High"
    )
    
    add_disease(
        name="Blackleg",
        symptoms="Sudden death,Swollen muscles,Fever,Lameness,Crackling sound under skin,Depression",
        description="An acute, infectious disease caused by Clostridium chauvoei. It typically affects young cattle (6-24 months) and is characterized by gas-filled swellings in large muscle groups.",
        precautions="Vaccination,Proper disposal of dead animals,Good pasture management,Avoid areas with known Blackleg history",
        severity="High"
    )
    
    add_disease(
        name="Johne's Disease",
        symptoms="Diarrhea,Weight loss despite good appetite,Reduced milk production,Weakness,Swelling under jaw",
        description="A chronic, contagious bacterial disease that affects the intestines of ruminants. Caused by Mycobacterium avium subspecies paratuberculosis.",
        precautions="Test and cull program,Good hygiene at calving,Feed calves colostrum from test-negative cows,Raise calves separately from adults,Control manure contamination",
        severity="High"
    )
    
    add_disease(
        name="Leptospirosis",
        symptoms="Abortion,Stillbirths,Reduced milk production,Jaundice,Blood in urine,Fever",
        description="A bacterial disease caused by various Leptospira species that affects many animals including cattle. It can also be transmitted to humans.",
        precautions="Vaccination,Rodent control,Avoid contact with urine from infected animals,Proper drainage,Isolation of infected animals",
        severity="Medium"
    )
    
    add_disease(
        name="Bovine Tuberculosis",
        symptoms="Weight loss,Weakness,Intermittent fever,Coughing,Enlarged lymph nodes,Reduced appetite",
        description="A chronic infectious disease caused by Mycobacterium bovis, which can spread to humans through consumption of unpasteurized dairy products.",
        precautions="Test and slaughter programs,Pasteurization of milk,Quarantine of new animals,Proper ventilation,Regular testing",
        severity="High"
    )
    
    add_disease(
        name="Anthrax",
        symptoms="Sudden death,Blood from orifices,High fever,Staggering,Convulsions,Difficult breathing",
        description="An acute infectious disease caused by Bacillus anthracis. It can affect most warm-blooded animals, including humans.",
        precautions="Vaccination in endemic areas,Proper disposal of dead animals,Avoid opening carcasses of suspected cases,Report to authorities immediately",
        severity="High"
    )
    
    add_disease(
        name="Salmonellosis",
        symptoms="Diarrhea,Fever,Dehydration,Weakness,Abortion,Reduced milk production",
        description="A disease caused by Salmonella bacteria that affects the intestinal tract and can cause severe diarrhea and dehydration.",
        precautions="Isolate sick animals,Proper sanitation,Testing of new additions,Clean water sources,Proper manure management",
        severity="Medium"
    )
    
    add_disease(
        name="Bovine Anaplasmosis",
        symptoms="Anemia,Jaundice,Weakness,Reduced milk production,Weight loss,Abortion",
        description="A vector-borne, infectious blood disease caused by Anaplasma marginale, which affects red blood cells.",
        precautions="Tick control,Proper needle hygiene,Vaccination in endemic areas,Testing new animals,Chemical control of vectors",
        severity="Medium"
    )
    
    # Viral Diseases
    add_disease(
        name="Bovine Viral Diarrhea (BVD)",
        symptoms="Diarrhea,Fever,Respiratory problems,Abortion,Birth defects,Mucosal lesions",
        description="A viral disease affecting cattle worldwide. It can cause a variety of symptoms and has a significant economic impact due to reproductive losses.",
        precautions="Vaccination,Biosecurity measures,Testing and removal of persistently infected animals,Quarantine new animals",
        severity="High"
    )
    
    add_disease(
        name="Infectious Bovine Rhinotracheitis (IBR)",
        symptoms="Nasal discharge,Coughing,Conjunctivitis,Fever,Reduced milk production,Abortion",
        description="A highly contagious respiratory disease caused by bovine herpesvirus 1 (BHV-1). It can affect cattle of all ages.",
        precautions="Vaccination,Isolation of new animals,Minimize stress,Good ventilation,Prompt treatment of secondary infections",
        severity="Medium"
    )
    
    add_disease(
        name="Foot and Mouth Disease",
        symptoms="Blisters on feet and mouth,Excessive salivation,Fever,Lameness,Reduced milk production,Weight loss",
        description="A highly contagious viral disease that affects cloven-hoofed animals. It's a reportable disease due to its economic impact.",
        precautions="Movement restrictions,Vaccination in endemic areas,Strict biosecurity,Culling of infected animals,Disinfection of premises",
        severity="High"
    )
    
    add_disease(
        name="Bovine Leukosis (BLV)",
        symptoms="Enlarged lymph nodes,Weight loss,Decreased milk production,Weakness,Anorexia,Rear limb weakness",
        description="A retroviral infection that causes a form of cancer called 'enzootic bovine leukosis' in cattle.",
        precautions="Test and segregate positive animals,Use clean needles for each animal,Pasteurize colostrum,Control biting insects,Avoid blood contamination",
        severity="Medium"
    )
    
    add_disease(
        name="Bovine Papillomavirus (Warts)",
        symptoms="Warts on skin and teats,Occasionally oral warts,Can affect young cattle more severely",
        description="A viral disease that causes benign tumors (warts) in cattle, usually self-limiting but can cause economic losses.",
        precautions="Isolation of affected animals,Avoid sharing equipment,Vaccines for specific virus types,Surgical removal of large warts",
        severity="Low"
    )
    
    add_disease(
        name="Rabies",
        symptoms="Behavioral changes,Aggression,Excessive salivation,Paralysis,Difficulty swallowing,Disorientation",
        description="A fatal viral disease affecting the central nervous system of warm-blooded animals, including cattle and humans.",
        precautions="Vaccination,Avoid contact with wildlife,Report suspicious behavior,Isolate suspicious animals,Post-exposure treatment for humans",
        severity="High"
    )
    
    add_disease(
        name="Rinderpest",
        symptoms="High fever,Oral erosions,Diarrhea,Dehydration,Nasal discharge,Death",
        description="A highly contagious viral disease (now eradicated globally) that affected cattle, buffalo, and other ruminants.",
        precautions="Vaccination (historically),Movement control,Quarantine,Culling of infected animals,Proper disposal of carcasses",
        severity="High"
    )
    
    # Parasitic Diseases
    add_disease(
        name="Liver Fluke Disease",
        symptoms="Weight loss,Reduced milk production,Anemia,Bottle jaw,Diarrhea,Lethargy",
        description="A parasitic disease caused by liver flukes (Fasciola hepatica) that damages the liver and bile ducts.",
        precautions="Strategic deworming,Drainage of wet areas,Fencing off wet areas,Rotational grazing,Regular fecal testing",
        severity="Medium"
    )
    
    add_disease(
        name="Bovine Coccidiosis",
        symptoms="Bloody diarrhea,Dehydration,Weight loss,Weakness,Straining to defecate,Anemia",
        description="An intestinal disease caused by coccidia parasites, typically affecting young cattle and causing damage to the intestinal lining.",
        precautions="Proper sanitation,Avoid overcrowding,Coccidiostats in feed,Clean water sources,Stress reduction",
        severity="Medium"
    )
    
    add_disease(
        name="Lungworm Disease",
        symptoms="Coughing,Difficulty breathing,Weight loss,Reduced milk production,Nasal discharge,Secondary pneumonia",
        description="A parasitic disease caused by Dictyocaulus viviparus that affects the lungs and can lead to severe respiratory problems.",
        precautions="Strategic deworming,Pasture rotation,Avoid damp pastures,Vaccination,Regular monitoring",
        severity="Medium"
    )
    
    add_disease(
        name="Tick-borne Diseases",
        symptoms="Fever,Anemia,Weakness,Jaundice,Weight loss,Reduced milk production",
        description="Various diseases transmitted by ticks, including babesiosis, anaplasmosis, and theileriosis.",
        precautions="Regular inspection for ticks,Acaricide application,Pasture management,Strategic dipping,Biological control",
        severity="Medium"
    )
    
    add_disease(
        name="Cryptosporidiosis",
        symptoms="Diarrhea,Lethargy,Dehydration,Reduced growth,Abdominal pain,Poor appetite",
        description="A parasitic disease that causes gastrointestinal illness and diarrhea, primarily affecting young calves.",
        precautions="Good hygiene,Proper waste management,Isolation of infected animals,Clean water sources,Colostrum management",
        severity="Medium"
    )
    
    # Metabolic and Nutritional Diseases
    add_disease(
        name="Milk Fever (Hypocalcemia)",
        symptoms="Muscle tremors,Weakness,Cold ears,Difficulty rising,Collapse,Coma",
        description="A metabolic disorder in dairy cows after calving, characterized by low blood calcium levels.",
        precautions="Proper transition period diet,Calcium supplementation,DCAD diet management,Injectable calcium for at-risk cows,Proper body condition",
        severity="High"
    )
    
    add_disease(
        name="Ketosis",
        symptoms="Reduced appetite,Weight loss,Decreased milk production,Sweet breath odor,Nervous behavior,Constipation",
        description="A metabolic disorder caused by negative energy balance, typically occurring in early lactation dairy cows.",
        precautions="Proper transition period feeding,Body condition monitoring,Propylene glycol supplementation,Energy-dense diets,Regular monitoring",
        severity="Medium"
    )
    
    add_disease(
        name="Grass Tetany (Hypomagnesemia)",
        symptoms="Muscle tremors,Excitability,Staggering,Convulsions,Collapse,Death",
        description="A metabolic disorder characterized by low blood magnesium levels, typically occurring when cattle graze lush, rapidly growing grasses.",
        precautions="Magnesium supplementation,Balanced fertilization of pastures,Legume-grass mixtures,Access to hay during risk periods",
        severity="High"
    )
    
    add_disease(
        name="Ruminal Acidosis",
        symptoms="Reduced appetite,Diarrhea,Reduced rumination,Lameness,Decreased milk production,Dehydration",
        description="A digestive disorder caused by the consumption of excessive amounts of rapidly fermentable carbohydrates leading to acid accumulation in the rumen.",
        precautions="Proper transition to high-grain diets,Adequate fiber in diet,Buffer supplementation,Regular feeding schedule,Proper feed mixing",
        severity="Medium"
    )
    
    add_disease(
        name="Bloat",
        symptoms="Swollen abdomen,Difficulty breathing,Discomfort,Excessive salivation,Kicking at belly,Collapse",
        description="A digestive disorder characterized by an excessive accumulation of gas in the rumen, which can't be expelled normally.",
        precautions="Avoid sudden access to lush legumes,Feed dry hay before grazing,Anti-bloat agents,Strip grazing,Plant diverse pastures",
        severity="High"
    )
    
    add_disease(
        name="Displaced Abomasum",
        symptoms="Reduced appetite,Decreased milk production,Pinging sound on left flank,Weight loss,Reduced rumination,Mild colic",
        description="A condition where the abomasum (true stomach) becomes filled with gas and moves from its normal position on the right side of the abdomen.",
        precautions="Proper transition period management,Adequate fiber in diet,Minimize stress at calving,Proper body condition,Regular feeding schedule",
        severity="Medium"
    )
    
    add_disease(
        name="Copper Deficiency",
        symptoms="Poor growth,Faded coat color,Anemia,Reduced reproduction,Diarrhea,Bone abnormalities",
        description="A nutritional deficiency that can lead to various health problems, particularly in areas with low soil copper or high molybdenum.",
        precautions="Mineral supplementation,Soil testing,Liver copper testing,Balanced mineral program,Injectable copper when needed",
        severity="Medium"
    )
    
    add_disease(
        name="Vitamin A Deficiency",
        symptoms="Night blindness,Reproductive failure,Poor growth,Rough hair coat,Increased susceptibility to infections,Diarrhea",
        description="A nutritional deficiency that can occur when cattle consume low-quality forages for extended periods.",
        precautions="Green forages in diet,Vitamin A supplementation,Proper feed storage,Regular assessment of feed quality",
        severity="Medium"
    )
    
    # Reproductive and Developmental Diseases
    add_disease(
        name="Retained Placenta",
        symptoms="Failure to expel placenta,Foul-smelling discharge,Fever,Reduced appetite,Decreased milk production",
        description="A condition where the placenta is not expelled within 24 hours after calving.",
        precautions="Proper nutrition during dry period,Minimize calving stress,Proper calcium and selenium levels,Monitor difficult births,Prompt veterinary care",
        severity="Medium"
    )
    
    add_disease(
        name="Metritis",
        symptoms="Foul-smelling uterine discharge,Fever,Reduced appetite,Decreased milk production,Dehydration,Lethargy",
        description="An inflammation of the uterus, usually due to bacterial infection after calving.",
        precautions="Clean calving environment,Good hygiene during assisted calvings,Proper nutrition,Early treatment of retained placenta,Regular post-calving checks",
        severity="Medium"
    )
    
    add_disease(
        name="Dystocia (Difficult Calving)",
        symptoms="Prolonged labor,Straining without progress,Visible feet/tail but no progress,Cow lying down repeatedly,Exhaustion,Bloody discharge",
        description="Difficulty in calving, which can be due to calf size, calf position, or maternal factors.",
        precautions="Breed selection for calving ease,Proper heifer development,Nutrition management,Regular pregnancy checks,Veterinary assistance when needed",
        severity="High"
    )
    
    add_disease(
        name="Joint Ill (Navel Ill)",
        symptoms="Swollen joints,Lameness,Fever,Reduced appetite,Navel infection,Lethargy",
        description="A bacterial infection in newborn calves, typically entering through the navel cord and affecting the joints.",
        precautions="Proper navel disinfection,Clean calving environment,Ensure adequate colostrum intake,Proper bedding,Early treatment",
        severity="Medium"
    )
    
    add_disease(
        name="White Muscle Disease",
        symptoms="Stiffness,Weakness,Unable to stand,Heart failure,Difficulty breathing,Sudden death",
        description="A nutritional myopathy caused by selenium and/or vitamin E deficiency, affecting skeletal and cardiac muscles.",
        precautions="Selenium supplementation in deficient areas,Vitamin E supplementation,Injectable selenium/vitamin E for newborns,Proper feed analysis",
        severity="Medium"
    )
    
    add_disease(
        name="Bovine Spongiform Encephalopathy (BSE)",
        symptoms="Behavioral changes,Nervousness,Aggression,Abnormal posture,Difficulty standing,Progressive deterioration",
        description="A fatal neurodegenerative disease of cattle, also known as 'mad cow disease.' It's a reportable disease with zoonotic potential.",
        precautions="Feed regulations,Surveillance programs,Proper disposal of suspect animals,No feeding of ruminant proteins to ruminants",
        severity="High"
    )
    
    # Less common or regionally specific diseases
    add_disease(
        name="Lumpy Skin Disease",
        symptoms="Nodules on skin,Fever,Nasal discharge,Reduced milk production,Enlarged lymph nodes,Lameness",
        description="A viral disease characterized by nodules on the skin, transmitted by blood-feeding insects.",
        precautions="Vaccination,Vector control,Quarantine of new animals,Movement restrictions,Report to authorities",
        severity="Medium"
    )
    
    add_disease(
        name="Wooden Tongue",
        symptoms="Swollen tongue,Excessive salivation,Difficulty eating,Weight loss,Reduced milk production,Bad breath",
        description="A bacterial infection caused by Actinobacillus lignieresii that causes inflammation and hardening of the tongue.",
        precautions="Avoid sharp objects in feed,Proper feed processing,Early treatment with antibiotics,Regular feed inspection",
        severity="Medium"
    )
    
    add_disease(
        name="Contagious Bovine Pleuropneumonia",
        symptoms="Coughing,Chest pain,Fever,Difficulty breathing,Nasal discharge,Weight loss",
        description="A contagious bacterial disease that affects the lungs and pleural cavity of cattle.",
        precautions="Quarantine,Movement controls,Vaccination,Culling of infected animals,Surveillance",
        severity="High"
    )
    
    add_disease(
        name="Pinkeye (Infectious Bovine Keratoconjunctivitis)",
        symptoms="Excessive tearing,Squinting,Cloudy cornea,Ulceration,Red/inflamed eye,Light sensitivity",
        description="A common, contagious eye infection caused by Moraxella bovis, exacerbated by dust, flies, and UV radiation.",
        precautions="Fly control,Reduce dust,Provide shade,Isolate affected animals,Early treatment,Vaccination",
        severity="Medium"
    )
    
    add_disease(
        name="Hardware Disease",
        symptoms="Reduced appetite,Weight loss,Reluctance to move,Arched back,Grunt when rising,Reduced milk production",
        description="A condition where cattle swallow metallic foreign objects that penetrate the reticulum, potentially damaging the heart or diaphragm.",
        precautions="Magnet placement in reticulum,Clean feed areas,Use of metal detectors in feed,Avoid metal contamination of feed",
        severity="Medium"
    )
    
    # Commit all changes to the database
    db.session.commit()
    print("Database populated with cattle diseases!")

# Run the function to populate the database
if __name__ == "__main__":
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Populate the database with diseases
        populate_diseases()
        
        # Print count of diseases in database
        count = CattleDisease.query.count()
        print(f"Total diseases in database: {count}")