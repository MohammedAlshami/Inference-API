from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from Mongodb import MongoDBHandler


app = Flask(__name__)

# Basic event tracking state storage (in memory)
mongo_handler = MongoDBHandler()

user_states = {}

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot_handler():
    """Handle incoming messages from WhatsApp."""
    incoming_msg = request.form.get('Body').strip().lower()
    from_number = request.form.get('From')
    response = MessagingResponse()
    msg = response.message()

    # Initialize user state if not already set
    if from_number not in user_states:
        user_states[from_number] = {'step': 'menu'}
    
    # Get the current step for this user
    current_step = user_states[from_number]['step']

    # Step 1: Show menu options
    if current_step == 'menu':
        if 'report' in incoming_msg:
            user_states[from_number]['step'] = 'event_type'
            msg.body("What type of event are you reporting?\n1. Floods\n2. Landslide\n3. Wildfire")
        elif 'cancel' in incoming_msg:
            msg.body("Your report has been canceled. Type 'Report' to start over.")
            user_states[from_number] = {'step': 'menu'}  # Reset to initial state
        else:
            msg.body("Welcome! Type 'Report' to report an event or 'Cancel' to exit.")

    # Step 2: Select event type
    elif current_step == 'event_type':
        if '1' in incoming_msg:
            user_states[from_number]['event'] = 'Floods'
            user_states[from_number]['step'] = 'location'
            msg.body("You selected 'Floods'. Please share your location.")
        elif '2' in incoming_msg:
            user_states[from_number]['event'] = 'Landslide'
            user_states[from_number]['step'] = 'location'
            msg.body("You selected 'Landslide'. Please share your location.")
        elif '3' in incoming_msg:
            user_states[from_number]['event'] = 'Wildfire'
            user_states[from_number]['step'] = 'location'
            msg.body("You selected 'Wildfire'. Please share your location.")
        else:
            msg.body("Invalid option. Please type 1, 2, or 3 to select an event type.")

    # Step 3: Handle location sharing
    elif current_step == 'location':
        if request.form.get("Latitude") and request.form.get("Longitude"):
            # Capture location data
            latitude = float(request.form.get("Latitude"))
            longitude = float(request.form.get("Longitude"))
            event_type = user_states[from_number].get('event', 'unknown event')

            # Fetch address from coordinates
            address = get_address_from_coordinates(latitude, longitude)

            # Save data to user state for later insertion
            user_states[from_number]['location'] = {"latitude": latitude, "longitude": longitude}
            user_states[from_number]['address'] = address

            # Ask for additional details
            user_states[from_number]['step'] = 'extra_details'
            msg.body(f"Thank you for reporting.\n"
                     f"Event type: {event_type}\n"
                     f"Location: {address}\n"
                     f"Do you have any additional details to add?")
        else:
            msg.body("Please use WhatsApp's location sharing feature to send your location.")

    # Step 4: Capture extra details and finalize report
    elif current_step == 'extra_details':
        extra_details = incoming_msg if incoming_msg else "No additional details provided"
        event_type = user_states[from_number]['event']
        location = user_states[from_number]['location']
        address = user_states[from_number]['address']

        # Construct record with all collected details
        record = {
            "type": "Feature",
            "properties": {
                "category": "request_for_help",
                "phone": from_number,
                "disaster_type": event_type.lower(),
                "details": extra_details,
                "address": address
            },
            "geometry": {
                "type": "Point",
                "coordinates": [location["longitude"], location["latitude"]]
            }
            
            
            
        }

        # Insert the report into MongoDB
        mongo_handler.insert_json(record, "Natural_diaster_events")

        # Acknowledge report completion and reset user state
        msg.body("Thank you for your report. Your information has been logged.")
        user_states[from_number] = {'step': 'menu'}  # Reset to menu

    return str(response)