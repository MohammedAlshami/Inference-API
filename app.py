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
            # Capture and print location data
            latitude = request.form.get("Latitude")
            longitude = request.form.get("Longitude")
            event_type = user_states[from_number].get('event', 'unknown event')
            print(f"User reported {event_type} at location: Latitude - {latitude}, Longitude - {longitude}")

            # Acknowledge receipt and reset user state
            msg.body("Thank you for reporting. We have received your location.")
            user_states[from_number] = {'step': 'menu'}
        else:
            msg.body("Please use WhatsApp's location sharing feature to send your location.")

    return str(response)


if __name__ == '__main__':
    # Use environment variables for Twilio keys in production
    app.run(debug=True)
