from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import datetime
from app.core.config import get_settings
from temporalio.client import Client
import uuid
from app.workers.temporal.workflows.invitation_mail_workflow import InvitationEmailWorkflow

async def create_temporal_client():
    return await Client.connect(get_settings().TEMPORAL_URL)

async def start_invitation_email_workflow(user_email: str, team_name: str, team_code: str):
    task_id = uuid.uuid4().hex
    client = await create_temporal_client()
    invitation_email_workflow = await client.execute_workflow(
        InvitationEmailWorkflow.run,
        id=task_id,
        task_queue="invitation-email-task-queue",
        args=(user_email, team_name, team_code)
    )
    return invitation_email_workflow

def send_team_invitation(user_email, username, team_name, team_code, sender_email, sender_password, smtp_server="smtp.gmail.com", smtp_port=587):
    """
    Send a professional team invitation email with team details
    
    Parameters:
    - user_email: Recipient's email address
    - username: Name of the invitee
    - team_name: Name of the team they're being invited to
    - team_code: Unique team access code
    - sender_email: Sender's email address
    - sender_password: Sender's email password
    - smtp_server: SMTP server address (default: smtp.gmail.com)
    - smtp_port: SMTP port (default: 587)
    
    Returns:
    - Boolean indicating whether the email was sent successfully
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Join {team_name} - Team Invitation"
    msg['From'] = sender_email
    msg['To'] = user_email

    html = f"""
    <html>
        <body style="font-family: 'Arial', sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff;">
            <div style="background-color: #f8fafc; padding: 40px; text-align: center;">
                <h1 style="color: #1e293b; margin: 0; font-size: 28px;">
                    Team Invitation
                </h1>
                <p style="color: #475569; font-size: 16px; margin-top: 10px;">
                    You've been invited to join {team_name}
                </p>
            </div>
            
            <div style="padding: 40px; background: white; border: 1px solid #e2e8f0; margin: 20px;">
                <p style="color: #1e293b; font-size: 16px; margin-bottom: 25px;">
                    Dear {username},
                </p>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin-bottom: 25px;">
                    We're pleased to invite you to join our team on our collaborative platform. Your expertise and 
                    contributions will be valuable additions to our team.
                </p>

                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 25px; margin: 30px 0;">
                    <h3 style="color: #1e293b; margin-top: 0; font-size: 18px;">
                        Team Details
                    </h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <tr>
                            <td style="padding: 8px 0; color: #475569; width: 120px;">Team Name:</td>
                            <td style="padding: 8px 0; color: #1e293b; font-weight: 500;">{team_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #475569;">Team Code:</td>
                            <td style="padding: 8px 0; color: #1e293b; font-weight: 500; font-family: monospace; font-size: 16px;">{team_code}</td>
                        </tr>
                    </table>
                </div>

                <div style="text-align: center; margin: 35px 0;">
                    <a href="#" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 16px;">
                        Accept Invitation
                    </a>
                </div>

                <p style="color: #475569; font-size: 14px; line-height: 1.6; margin-top: 25px;">
                    If the button above doesn't work, you can use the team code to join directly through the platform.
                </p>

                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">

                <p style="color: #64748b; font-size: 14px; line-height: 1.6;">
                    This invitation was sent to {user_email}. If you received this by mistake, please ignore this email.
                </p>
            </div>
            
            <div style="background-color: #f8fafc; padding: 20px; text-align: center;">
                <p style="color: #64748b; margin: 0; font-size: 14px;">
                    © {datetime.now().year} {team_name}. All rights reserved.
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