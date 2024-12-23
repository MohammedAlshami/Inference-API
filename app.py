from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

# In-memory state tracking (Use a database for persistence in production)
user_states = {}

def detect_ripeness(image_url):
    # Placeholder function: Replace with actual implementation
    return "https://myhackathon1.vercel.app/detection_sample.png"

def detect_disease(image_url):
    # Placeholder function: Replace with actual implementation
    return "https://myhackathon1.vercel.app/detection_sample.png"

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot_handler():
    """Handle incoming messages from WhatsApp."""
    incoming_msg = request.form.get('Body', '').strip().lower()
    from_number = request.form.get('From')
    media_url = request.form.get('MediaUrl0')  # URL of the image sent by the user
    response = MessagingResponse()
    msg = response.message()

    # Initialize user state if not already set
    if from_number not in user_states:
        user_states[from_number] = {'step': 'menu'}

    # Get the current step for this user
    current_step = user_states[from_number]['step']

    if current_step == 'menu':
        if media_url:
            user_states[from_number] = {'step': 'awaiting_selection', 'image_url': media_url}
            msg.body(
                "What would you like to do? Reply with:\n"
                "1 for Ripeness Detection\n"
                "2 for Disease Detection"
            )
        else:
            msg.body("Please send an image to start.")

    elif current_step == 'awaiting_selection':
        image_url = user_states[from_number].get('image_url')
        if incoming_msg == '1':
            processed_image_url = detect_ripeness(image_url)
            msg.body("Ripeness detection completed. Here is the result:")
            msg.media(processed_image_url)
        elif incoming_msg == '2':
            processed_image_url = detect_disease(image_url)
            msg.body("Disease detection completed. Here is the result:")
            msg.media(processed_image_url)
        else:
            msg.body("Invalid selection. Reply with:\n1 for Ripeness Detection\n2 for Disease Detection")
            return str(response)

        # Reset to menu after processing
        user_states[from_number] = {'step': 'menu'}

    return str(response)

if __name__ == '__main__':
    app.run(debug=True)
