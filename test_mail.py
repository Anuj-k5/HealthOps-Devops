from app import create_app, mail
from flask_mail import Message
import traceback

app = create_app()
with app.app_context():
    try:
        msg = Message('Test', recipients=['varunbedaka1780@gmail.com'])
        msg.body = 'Test'
        mail.send(msg)
        print("Success!")
    except Exception as e:
        traceback.print_exc()
