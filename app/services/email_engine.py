import os
import markdown  # NEW: We need this to convert ## to <h2> and ** to <b>
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from dotenv import load_dotenv

load_dotenv()

# Email Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def send_draft_email(recipient: EmailStr, subject: str, body_text: str):
    """
    Sends the draft as a formatted HTML email.
    Converts Markdown (##, **) into HTML (<h2>, <b>) automatically.
    """
    
    # 1. Convert Markdown to HTML
    # This turns "## Header" into "<h2>Header</h2>" and "**Bold**" into "<strong>Bold</strong>"
    formatted_html_content = markdown.markdown(body_text)

    # 2. Wrap it in a Professional Email Template (Inline CSS for Email Clients)
    email_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            /* Basic resets for email clients */
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333333; }}
            h1, h2, h3 {{ color: #000000; margin-top: 20px; border-bottom: 1px solid #eeeeee; padding-bottom: 5px; }}
            p {{ margin-bottom: 15px; }}
            strong {{ font-weight: bold; color: #000; }}
            blockquote {{ 
                border-left: 4px solid #4F8BF9; 
                margin-left: 0; 
                padding-left: 15px; 
                color: #555; 
                font-style: italic; 
                background-color: #f9f9f9;
                padding: 10px;
            }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 5px; }}
            .container {{
                max-width: 700px;
                margin: 0 auto;
                padding: 20px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #ffffff;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 12px;
                color: #888888;
                text-align: center;
                border-top: 1px solid #eeeeee;
                padding-top: 10px;
            }}
        </style>
    </head>
    <body style="background-color: #f4f4f4; padding: 20px;">
        
        <div class="container">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #4F8BF9; border: none;">LexFlow Draft Document</h2>
            </div>

            <div>
                {formatted_html_content}
            </div>

            <div class="footer">
                <p>Generated via LexFlow AI - Drafting Studio</p>
                <p>This is an automated draft. Please review before official use.</p>
            </div>
        </div>

    </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=email_template,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return True