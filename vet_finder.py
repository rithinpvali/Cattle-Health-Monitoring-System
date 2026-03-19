import math
from app import db
from models import Veterinarian

def find_nearby_vets(latitude=None, longitude=None, max_results=3):
    """
    Find nearby veterinarians. If coordinates are not provided,
    returns a selection of available vets.
    
    Args:
        latitude (float, optional): User's latitude
        longitude (float, optional): User's longitude
        max_results (int, optional): Maximum number of results to return
        
    Returns:
        list: List of Veterinarian objects
    """
    # If coordinates are provided, find vets by distance
    if latitude and longitude:
        vets = Veterinarian.query.all()
        
        # Calculate distance and sort vets
        vets_with_distance = []
        for vet in vets:
            if vet.latitude and vet.longitude:
                distance = calculate_distance(latitude, longitude, vet.latitude, vet.longitude)
                vets_with_distance.append((vet, distance))
        
        # Sort by distance
        vets_with_distance.sort(key=lambda x: x[1])
        
        # Return the closest vets
        return [vet for vet, _ in vets_with_distance[:max_results]]
    
    # Otherwise, just return some vets
    else:
        return Veterinarian.query.limit(max_results).all()

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points using the Haversine formula
    """
    # Radius of the Earth in kilometers
    R = 6371.0
    
    # Convert coordinates to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance
