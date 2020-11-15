from fastapi import FastAPI
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME="users.svgame",
    MAIL_PASSWORD="abe19ffdb6760f9822",
    MAIL_FROM="users.svgame@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False
)

app = FastAPI()


def html(frontURL, code):
    return f"""
<p>Thanks for creating a new user in the Secret Voldemort's game!</p>
<p>Click <a href={frontURL + code}>here</a> to activate your account.</p>
"""


async def simple_send(email, code="", front_url="") -> JSONResponse:
    print(email)
    message = MessageSchema(
        subject="Activate your secret voldemort account",
        recipients=email,
        body=html(front_url, code),
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    return JSONResponse(status_code=200, content={"message": "email has been sent"})
