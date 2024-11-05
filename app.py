from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os
import json

app = Flask(__name__)

# Twilio credentials - replace with your actual credentials
TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_PHONE_NUMBER = 'whatsapp:+14155238886'  # Your Twilio WhatsApp number

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Basic event tracking state storage (in memory)
user_states = {}

def send_interactive_message(to_number, message_type, content):
    """Helper function to send interactive messages"""
    if message_type == "menu":
        message = client.messages.create(
            from_=TWILIO_PHONE_NUMBER,
            to=to_number,
            body="Welcome! Please select an option:",
            media_url=['https://media.tenor.com/7dr3AgyEiN0AAAAj/anime-girl-wave.gif'],
            options=[
                {
                    "type": "list",
                    "label": "Main Menu",
                    "options": [
                        {
                            "label": "Report an Event",
                            "value": "report",
                            "description": "Report a new incident"
                        },
                        {
                            "label": "Cancel",
                            "value": "cancel",
                            "description": "Cancel the current operation"
                        }
                    ]
                }
            ]
        )
    elif message_type == "event_type":
        message = client.messages.create(
            from_=TWILIO_PHONE_NUMBER,
            to=to_number,
            body="What type of event are you reporting?",
            options=[
                {
                    "type": "list",
                    "label": "Event Types",
                    "options": [
                        {
                            "label": "Floods",
                            "value": "1",
                            "description": "Report flooding incident"
                        },
                        {
                            "label": "Landslide",
                            "value": "2",
                            "description": "Report landslide incident"
                        },
                        {
                            "label": "Wildfire",
                            "value": "3",
                            "description": "Report wildfire incident"
                        }
                    ]
                }
            ]
        )
    return message

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    """Handle incoming messages from WhatsApp."""
    # Get incoming message and sender info
    incoming_msg = request.form.get('Body', '').strip().lower()
    from_number = request.form.get('From')
    
    # Handle interactive message responses
    selection = None
    if 'ListTitle' in request.form:
        selection = request.form.get('ListSelection')
    
    response = MessagingResponse()
    msg = response.message()
    
    # Initialize user state if not already set
    if from_number not in user_states:
        user_states[from_number] = {'step': 'menu'}
        send_interactive_message(from_number, "menu", None)
        return str(response)
    
    # Get the current step for this user
    current_step = user_states[from_number]['step']
    
    # Handle different steps
    if current_step == 'menu':
        handle_menu(from_number, selection or incoming_msg, msg)
    elif current_step == 'event_type':
        handle_event_type(from_number, selection or incoming_msg, msg)
    elif current_step == 'location':
        handle_location(from_number, request, msg)
    else:
        # Reset state if something goes wrong
        user_states[from_number] = {'step': 'menu'}
        send_interactive_message(from_number, "menu", None)
    
    return str(response)

def handle_menu(from_number, incoming_msg, msg):
    """Handle menu selection"""
    if incoming_msg in ['1', 'report']:
        user_states[from_number]['step'] = 'event_type'
        send_interactive_message(from_number, "event_type", None)
    elif incoming_msg in ['2', 'cancel']:
        user_states[from_number] = {'step': 'menu'}
        msg.body("Your report has been canceled. Send any message to start over.")
        send_interactive_message(from_number, "menu", None)
    else:
        send_interactive_message(from_number, "menu", None)

def handle_event_type(from_number, incoming_msg, msg):
    """Handle event type selection"""
    event_types = {
        '1': 'Floods',
        '2': 'Landslide',
        '3': 'Wildfire'
    }
    
    if incoming_msg in event_types:
        user_states[from_number].update({
            'event': event_types[incoming_msg],
            'step': 'location'
        })
        msg.body(f"You selected '{event_types[incoming_msg]}'. Please share your location using WhatsApp's location sharing feature.")
    else:
        send_interactive_message(from_number, "event_type", None)

def handle_location(from_number, request, msg):
    """Handle location data"""
    latitude = request.form.get("Latitude")
    longitude = request.form.get("Longitude")
    
    if latitude and longitude:
        event_type = user_states[from_number].get('event', 'unknown event')
        # Log the location data
        print(f"User reported {event_type} at location: Latitude - {latitude}, Longitude - {longitude}")
        
        # Send confirmation and reset state
        msg.body(f"Thank you for reporting the {event_type}. Your location has been received and recorded.\n\nSend any message to report another event.")
        user_states[from_number] = {'step': 'menu'}
        send_interactive_message(from_number, "menu", None)
    else:
        msg.body("Please use WhatsApp's location sharing feature to send your location.")
