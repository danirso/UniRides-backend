from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings


conf = ConnectionConfig(
    MAIL_USERNAME = settings.MAIL_USERNAME,
    MAIL_PASSWORD = settings.MAIL_PASSWORD,
    MAIL_FROM = settings.MAIL_FROM,
    MAIL_PORT = settings.MAIL_PORT,
    MAIL_SERVER = settings.MAIL_SERVER,
    MAIL_FROM_NAME = settings.MAIL_FROM_NAME,
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

def send_activation_email(email_to: str, user_name: str, token: str, background_tasks: BackgroundTasks):
    
    verification_link = f"{settings.API_BASE_URL}/auth/verify-email?token={token}"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
        <h2 style="color: #2E86C1;">Bem-vindo(a) ao Unirides!</h2>
        <p>Olá <strong>{user_name}</strong>,</p>
        <p>Para ativar sua conta, clique no botão abaixo.</p>
        <a href="{verification_link}" style="display: inline-block; padding: 10px 20px; color: white; background-color: #2E86C1; text-decoration: none; border-radius: 5px; margin-top: 10px;">Ativar minha conta no Unirides</a>
        <p style="margin-top: 20px; font-size: 12px; color: #777;">Este link é válido por 1 hora. Se você não se cadastrou no Unirides, apenas ignore este e-mail.</p>
    </div>
    """

    message = MessageSchema(
        subject="Ative sua conta no Unirides",
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)