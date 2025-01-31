from app.core.config import get_settings
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent

# Intializing mail configuation
mail_configuation = ConnectionConfig(
    MAIL_USERNAME = get_settings().MAIL_USERNAME,
    MAIL_PASSWORD = get_settings().MAIL_PASSWORD,
    MAIL_FROM = get_settings().MAIL_FROM,
    MAIL_PORT = get_settings().MAIL_PORT,
    MAIL_SERVER = get_settings().MAIL_SERVER,
    MAIL_FROM_NAME = get_settings().MAIL_FROM_NAME,
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    TEMPLATE_FOLDER= Path(BASE_DIR, 'templates')
)

mail = FastMail(
    config=mail_configuation
)

def create_message(recipients: List[str], subject: str, body: str):
    message = MessageSchema(
        recipients=recipients,
        subject=subject,
        body=body,
        subtype=MessageType.html
    )
    return message