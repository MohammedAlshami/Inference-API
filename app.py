from datetime import datetime, timedelta
import random
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request
import json

app = Flask(__name__)

class FarmBotWhatsApp:
    def __init__(self):
        # Twilio credentials
        self.account_sid = ''
        self.auth_token = ''
        self.client = Client(self.account_sid, self.auth_token)
        self.bot_number = 'whatsapp:+12313034992'  # Your Twilio WhatsApp number
        
        # Simulate pre-registered worker data
        self.worker_data = {
            'W123': {
                'id': 'W123',
                'name': 'John',
                'language': 'English',
                'phone': 'whatsapp:+601164504470'  # Worker's WhatsApp number
            }
        }
        
        # Task data with coordinates
        self.tasks = {
            'today': [
                {
                    'id': 1,
                    'description': 'Harvest Section A',
                    'status': 'pending',
                    'location': {'latitude': '37.7858', 'longitude': '-122.4064'}
                },
                {
                    'id': 2,
                    'description': 'Check irrigation System B',
                    'status': 'pending',
                    'location': {'latitude': '37.7859', 'longitude': '-122.4065'}
                }
            ],
            'this_week': [
                {
                    'id': 3,
                    'description': 'Fertilize Section C',
                    'status': 'pending',
                    'location': {'latitude': '37.7860', 'longitude': '-122.4066'}
                },
                {
                    'id': 4,
                    'description': 'Pest control in greenhouse',
                    'status': 'pending',
                    'location': {'latitude': '37.7861', 'longitude': '-122.4067'}
                }
            ]
        }
        
        # Store user states
        self.user_states = {}

    def send_main_menu(self, to_number):
        """Send main menu with WhatsApp buttons"""
        self.client.messages.create(
            from_=self.bot_number,
            to=to_number,
            body="Welcome to Farm Management Bot!\nPlease select an option:",
            interactive=[{
                "type": "button",
                "body": {
                    "text": "Choose an option"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "schedule",
                                "title": "View Schedule"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "report",
                                "title": "Report Crop Status"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "help",
                                "title": "Get Help"
                            }
                        }
                    ]
                }
            }]
        )

    def send_schedule_menu(self, to_number):
        """Send schedule menu with WhatsApp buttons"""
        self.client.messages.create(
            from_=self.bot_number,
            to=to_number,
            body="View Schedule:",
            interactive=[{
                "type": "button",
                "body": {
                    "text": "Select time period"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "today",
                                "title": "Today's Tasks"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "week",
                                "title": "This Week's Tasks"
                            }
                        }
                    ]
                }
            }]
        )

    def send_task_details(self, to_number, task_type):
        """Send task details with location"""
        tasks = self.tasks[task_type]
        for task in tasks:
            # Send task description
            self.client.messages.create(
                from_=self.bot_number,
                to=to_number,
                body=f"Task {task['id']}: {task['description']} - {task['status']}"
            )
            
            # Send location
            self.client.messages.create(
                from_=self.bot_number,
                to=to_number,
                content_sid='HLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',  # Placeholder for location content SID
                persistent_action=[f"geo:{task['location']['latitude']},{task['location']['longitude']}"]
            )
            
            if task['status'] == 'pending':
                self.client.messages.create(
                    from_=self.bot_number,
                    to=to_number,
                    interactive=[{
                        "type": "button",
                        "body": {
                            "text": f"Mark Task {task['id']} as complete?"
                        },
                        "action": {
                            "buttons": [
                                {
                                    "type": "reply",
                                    "reply": {
                                        "id": f"complete_{task['id']}",
                                        "title": "Yes"
                                    }
                                },
                                {
                                    "type": "reply",
                                    "reply": {
                                        "id": "no",
                                        "title": "No"
                                    }
                                }
                            ]
                        }
                    }]
                )

    def handle_crop_detection(self, to_number, media_url=None):
        """Handle crop detection workflow"""
        if not media_url:
            self.client.messages.create(
                from_=self.bot_number,
                to=to_number,
                body="Please send a photo of the crop for analysis."
            )
            return
        
        # Simulate AI analysis
        ripeness = random.choice(['Not Ripe', 'Nearly Ripe', 'Ready for Harvest'])
        confidence = random.randint(85, 99)
        
        # Send analysis results
        self.client.messages.create(
            from_=self.bot_number,
            to=to_number,
            body=f"Analysis Results:\nReceived Image: {media_url}\nRipeness: {ripeness}\nConfidence: {confidence}%"
        )

@app.route('/', methods=['POST'])
def webhook():
    bot = FarmBotWhatsApp()
    incoming_msg = request.values.get('Body', '').lower()
    media_url = request.values.get('MediaUrl0', None)
    from_number = request.values.get('From')
    
    resp = MessagingResponse()
    
    if media_url:
        bot.handle_crop_detection(from_number, media_url)
    elif incoming_msg in ['hi', 'hello', 'menu']:
        bot.send_main_menu(from_number)
    elif incoming_msg == 'schedule':
        bot.send_schedule_menu(from_number)
    elif incoming_msg in ['today', 'week']:
        task_type = 'today' if incoming_msg == 'today' else 'this_week'
        bot.send_task_details(from_number, task_type)
    elif incoming_msg.startswith('complete_'):
        task_id = int(incoming_msg.split('_')[1])
        # Update task status logic here
        resp.message(f"Task {task_id} marked as complete!")
    
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)