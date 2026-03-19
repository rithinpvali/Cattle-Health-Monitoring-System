import os
import random
import logging
from twilio.rest import Client

def generate_otp(length=6):
    """Generate a random numeric OTP of specified length"""
    digits = "0123456789"
    otp = ""
    for _ in range(length):
        otp += random.choice(digits)
    return otp

def send_otp(phone_number, otp):
    """
    Send OTP via SMS using Twilio
    
    Note: In a production environment, this would use Twilio or a similar service.
    For development purposes, we'll just log the OTP.
    """
    # Get Twilio credentials from environment variables
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone = os.environ.get("TWILIO_PHONE_NUMBER")
    
    # If Twilio credentials are available, send SMS
    if account_sid and auth_token and twilio_phone:
        try:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=f"Your OTP for Cattle Health Monitoring is: {otp}",
                from_=twilio_phone,
                to=f"+91{phone_number}"  # Assuming Indian phone numbers
            )
            logging.info(f"OTP sent to {phone_number}, SID: {message.sid}")
            return True
        except Exception as e:
            logging.error(f"Failed to send OTP via Twilio: {str(e)}")
    
    # For development, just log the OTP
    logging.info(f"Development mode: OTP for {phone_number} is {otp}")
    return True
