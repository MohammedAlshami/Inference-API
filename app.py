from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import os
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# In-memory state tracking (Use a database for persistence in production)
user_states = {}

def detect_ripeness(image_url):
    image_url_with_detection = 'https://m.media-amazon.com/images/I/71bgp0-0swL._AC_UF894,1000_QL80_.jpg'
    return image_url_with_detection

def detect_disease(image_url):
    image_url_with_detection = 'https://m.media-amazon.com/images/I/71bgp0-0swL._AC_UF894,1000_QL80_.jpg'
    return image_url_with_detection

@app.before_request
def before_request():
    if 'HTTP_X_FORWARDED_PROTO' in request.environ:
        if request.environ['HTTP_X_FORWARDED_PROTO'] == 'https':
            request.scheme = 'https'

@app.route('/', methods=['GET', 'POST'])
def health_check():
    """Health check endpoint to verify the API status."""
    return jsonify({"status": "healthy", "service": "drangue-bot"}), 200

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot_handler():
    try:
        incoming_msg = request.form.get('Body', '').strip().lower()
        from_number = request.form.get('From')
        media_url = request.form.get('MediaUrl0')
        
        response = MessagingResponse()
        msg = response.message()

        if from_number not in user_states:
            user_states[from_number] = {'step': 'menu'}

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

            user_states[from_number] = {'step': 'menu'}

        return str(response)
    except Exception as e:
        app.logger.error(f"Error in whatsapp_bot_handler: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)