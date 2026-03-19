from app import db
from models import CattleDisease
import logging

def predict_disease(symptoms):
    """
    Predict disease based on symptoms matching, using weighted algorithm.
    
    Args:
        symptoms (list): List of symptoms observed in the cattle
        
    Returns:
        str: Name of the predicted disease
    """
    # Get all diseases from the database
    diseases = CattleDisease.query.all()
    
    if not diseases:
        logging.warning("No diseases found in database for prediction.")
        return "Unknown"
    
    # Convert symptoms to lowercase for case-insensitive matching
    normalized_symptoms = [s.lower().strip() for s in symptoms]
    
    # Stores results as (disease, score) tuples
    disease_scores = []
    
    # For each disease, calculate a matching score
    for disease in diseases:
        disease_symptoms = [s.lower().strip() for s in disease.symptoms.split(',')]
        
        # Skip diseases with no symptoms defined
        if not disease_symptoms:
            continue
        
        # Count exact matches
        exact_matches = sum(1 for symptom in normalized_symptoms if symptom in disease_symptoms)
        
        # Count partial matches (where a symptom contains or is contained by a disease symptom)
        partial_matches = 0
        for user_symptom in normalized_symptoms:
            for disease_symptom in disease_symptoms:
                # Skip symptoms already counted as exact matches
                if user_symptom == disease_symptom:
                    continue
                    
                # Check for partial matching (substring)
                if user_symptom in disease_symptom or disease_symptom in user_symptom:
                    partial_matches += 0.5  # Partial match has lower weight
                    break
        
        # Calculate various metrics
        symptom_coverage = exact_matches / len(disease_symptoms)
        reported_coverage = exact_matches / len(normalized_symptoms) if normalized_symptoms else 0
        
        # Calculate weighted score
        # - More weight to exact matches
        # - Some weight to partial matches
        # - Consider both disease coverage and reported coverage
        # - Add severity as a small factor
        score = (
            (exact_matches * 3) +  # Exact matches have higher weight
            (partial_matches * 1) +  # Partial matches have lower weight
            (symptom_coverage * 2) +  # Coverage of disease symptoms
            (reported_coverage * 1) +  # Coverage of reported symptoms
            (get_severity_score(disease.severity) * 0.3)  # Slight bias toward more severe diseases
        )
        
        # Add to results
        disease_scores.append((disease, score))
    
    # Sort by score in descending order
    disease_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Log top 3 matches for debugging (if available)
    if len(disease_scores) > 0:
        top_matches = disease_scores[:min(3, len(disease_scores))]
        logging.debug("Top disease matches:")
        for disease, score in top_matches:
            logging.debug(f"- {disease.name}: {score}")
    
    # Return the top disease or "Unknown" if no matches or very low score
    if disease_scores and disease_scores[0][1] > 1.0:  # Threshold for minimum confidence
        return disease_scores[0][0].name
    else:
        return "Unknown"

def get_severity_score(severity):
    """Convert severity string to numeric score for comparison"""
    severity_map = {
        "Low": 1,
        "Medium": 2,
        "High": 3
    }
    return severity_map.get(severity, 0)
