from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

# Basic event tracking state storage (in memory)
user_states = {}

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
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
        msg.body("Welcome! Please select an option:\n\n1. Report an event\n2. Cancel")
        msg.media('https://media.tenor.com/7dr3AgyEiN0AAAAj/anime-girl-wave.gif')  # Optional: Add an image for more context

    # Step 2: Process menu selection
    elif current_step == 'menu_selection':
        if 'report' in incoming_msg:
            user_states[from_number]['step'] = 'event_type'
            msg.body("What type of event are you reporting?\n\n1. Floods\n2. Landslide\n3. Wildfire")
        elif 'cancel' in incoming_msg:
            msg.body("Your report has been canceled. Type 'Report' to start over.")
            user_states[from_number] = {'step': 'menu'}  # Reset to initial state
        else:
            msg.body("Invalid selection. Please type 'Report' to report an event or 'Cancel' to exit.")

    # Step 3: Select event type
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

    # Step 4: Handle location sharing
    elif current_step == 'location':
        if request.form.get("Latitude") and request.form.get("Longitude"):
            latitude = request.form.get("Latitude")
            longitude = request.form.get("Longitude")
            event_type = user_states[from_number].get('event', 'unknown event')

            # Log the location data
            print(f"User reported {event_type} at location: Latitude - {latitude}, Longitude - {longitude}")

            # Acknowledge receipt and provide summary of information collected
            msg.body(f"Thank you for reporting!\n\nHere is your information:\n- Event Type: {event_type}\n- Location: Latitude - {latitude}, Longitude - {longitude}")
            
            # Reset user state
            user_states[from_number] = {'step': 'menu'}
        else:
            msg.body("Please use WhatsApp's location sharing feature to send your location.")

    return str(response)
