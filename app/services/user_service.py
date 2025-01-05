from passlib.context import CryptContext
from temporalio.client import Client
from app.core.config import get_settings
from app.workers.temporal.workflows.user_email_workflow import UserEmailWorkflow
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import secrets

pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

async def create_temporal_client():
    return await Client.connect(get_settings().TEMPORAL_URL)

async def start_email_workflow(user_email: str):
    task_id = uuid.uuid4().hex
    client = await create_temporal_client()
    email_workflow = await client.execute_workflow(
        UserEmailWorkflow.run,
        user_email,
        id=task_id,
        task_queue="user-email-task-queue"
    )
    return email_workflow

def generate_team_code() -> str:
    return secrets.token_hex(2).upper()

def send_welcome_email(user_email, username, sender_email, sender_password, smtp_server="smtp.gmail.com", smtp_port=587):
    """
    Send a styled welcome email to new users
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "🌟 Your AI Journey Begins Now! 🚀"
    msg['From'] = sender_email
    msg['To'] = user_email

    html = f"""
    <html>
        <body style="font-family: 'Arial', sans-serif; max-width: 600px; margin: 0 auto; background-color: #f9f9f9;">
            <div style="background: linear-gradient(120deg, #6b46c1 0%, #3b82f6 100%); padding: 40px; text-align: center; border-radius: 0 0 30px 30px;">
                <h1 style="color: white; margin: 0; font-size: 36px; text-shadow: 3px 3px 6px rgba(0,0,0,0.3);">
                    🎉 Welcome to the Future of AI! 🎉
                </h1>
                <p style="color: #e0e7ff; font-size: 18px; margin-top: 10px;">
                    Where Data Meets Intelligence
                </p>
            </div>
            
            <div style="padding: 30px; background: white; margin: 20px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
                <h2 style="background: linear-gradient(to right, #6b46c1, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 32px;">
                    Hello {username}! 👋
                </h2>
                
                <div style="background: linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%); padding: 25px; border-radius: 15px; margin: 25px 0;">
                    <p style="color: white; font-size: 20px; text-align: center; margin: 0; line-height: 1.6;">
                        "Chat with Your Data - Structured, Unstructured,<br>
                        <span style="font-size: 24px; font-weight: bold;">Anything is Possible!" ✨</span>
                    </p>
                </div>

                <div style="background: rgba(107, 70, 193, 0.1); border-radius: 15px; padding: 25px; margin: 20px 0;">
                    <h3 style="color: #6b46c1; margin-top: 0; text-align: center; font-size: 24px;">
                        🚀 Unleash the Power of AI
                    </h3>
                    <ul style="color: #4b5563; font-size: 16px; line-height: 2;">
                        <li>🤖 Advanced Chat with Any Data Format</li>
                        <li>📊 Real-time Data Analysis & Insights</li>
                        <li>🎯 Intelligent Pattern Recognition</li>
                        <li>🔄 Seamless Data Integration</li>
                    </ul>
                </div>

                <div style="background: linear-gradient(45deg, #3b82f6 0%, #6b46c1 100%); padding: 25px; border-radius: 15px; text-align: center;">
                    <p style="color: white; font-size: 18px; margin: 0;">
                        "Transform Your Data Into Intelligence"
                    </p>
                </div>
            </div>
            
            <div style="background: linear-gradient(120deg, #3b82f6 0%, #6b46c1 100%); padding: 25px; text-align: center; border-radius: 20px 20px 0 0;">
                <p style="color: white; margin: 0; line-height: 1.6;">
                    🌟 Your AI Adventure Awaits! 🌟<br>
                    <span style="font-size: 14px;">© {datetime.now().year} Next-Gen AI Platform</span>
                </p>
            </div>
        </body>
    </html>
    """

    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False