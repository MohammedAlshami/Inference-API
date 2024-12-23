from flask import Flask, request
from twilio.rest import Client
import os

app = Flask(__name__)

# Twilio credentials
account_sid = ""
auth_token = ""
twilio_whatsapp_number = 'whatsapp:+14155238886'

# Initialize Twilio client
client = Client(account_sid, auth_token)

# In-memory state tracking (Use a database for persistence in production)
user_states = {}

def send_menu_buttons(to_number):
    """
    Send a message with buttons for Ripeness and Disease Detection.
    """
    client.messages.create(
        from_=twilio_whatsapp_number,
        to=to_number,
        content_sid='YOUR_CONTENT_TEMPLATE_SID',  # Replace with your approved template SID
        content_variables={
            '1': 'Ripeness Detection',
            '2': 'Disease Detection'
        }
    )

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot_handler():
    """Handle incoming messages from WhatsApp."""
    incoming_msg = request.form.get('Body', '').strip().lower()
    from_number = request.form.get('From')
    media_url = request.form.get('MediaUrl0')  # URL of the image sent by the user

    # Initialize user state if not already set
    if from_number not in user_states:
        user_states[from_number] = {'step': 'menu'}

    current_step = user_states[from_number]['step']

    if current_step == 'menu':
        if media_url:
            user_states[from_number] = {'step': 'awaiting_selection', 'image_url': media_url}
            # Send buttons for options
            send_menu_buttons(from_number)
        else:
            client.messages.create(
                from_=twilio_whatsapp_number,
                to=from_number,
                body="Please send an image to start."
            )

    elif current_step == 'awaiting_selection':
        image_url = user_states[from_number].get('image_url')
        if incoming_msg == 'ripeness detection':  # Matches button text
            processed_image_url = detect_ripeness(image_url)
            client.messages.create(
                from_=twilio_whatsapp_number,
                to=from_number,
                body="Ripeness detection completed. Here is the result:",
                media_url=processed_image_url
            )
        elif incoming_msg == 'disease detection':  # Matches button text
            processed_image_url = detect_disease(image_url)
            client.messages.create(
                from_=twilio_whatsapp_number,
                to=from_number,
                body="Disease detection completed. Here is the result:",
                media_url=processed_image_url
            )
        else:
            send_menu_buttons(from_number)
            return ('', 204)

        # Reset user state to menu
        user_states[from_number] = {'step': 'menu'}

    return ('', 204)

def detect_ripeness(image_url):
    # Placeholder function: Replace with actual implementation
    return "https://myhackathon1.vercel.app/detection_sample.png"

def detect_disease(image_url):
    # Placeholder function: Replace with actual implementation
    return "https://myhackathon1.vercel.app/detection_sample.png"

if __name__ == '__main__':
    app.run(debug=True)
