from twilio.rest import Client
from django.conf import settings

def send_whatsapp_alert(message):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    client.messages.create(
        body=message,
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=settings.OWNER_WHATSAPP_NUMBER
    )
