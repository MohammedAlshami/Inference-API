from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from  FirebaseDetection import FirebaseDetection 

app = Flask(__name__)

# In-memory state tracking (Use a database for persistence in production)
user_states = {}



# Firebase Configuration
firebase_config = {
    "apiKey": "AIzaSyBLv1DiRB6egmpaoIKfjODXZF5fYheQKIM",
    "authDomain": "realtimedatabasetest-f226a.firebaseapp.com",
    "databaseURL": "https://realtimedatabasetest-f226a-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "realtimedatabasetest-f226a",
    "storageBucket": "realtimedatabasetest-f226a.appspot.com",
    "messagingSenderId": "348704796176",
    "appId": "1:348704796176:web:38994c5ab4d54b752ce495"
}

# Example usage
firebase_detection = FirebaseDetection(firebase_config)


def detect_ripeness(image_url):
    image_url_with_detection = firebase_detection.process_and_upload(image_url)

    # Placeholder function: Replace with actual implementation
    return image_url_with_detection

def detect_disease(image_url):
    image_url_with_detection = firebase_detection.process_and_upload(image_url)

    # Placeholder function: Replace with actual implementation
    return image_url_with_detection

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