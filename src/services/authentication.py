from fastapi_login import LoginManager
from src.models import User
from pony.orm import db_session
from itsdangerous import URLSafeTimedSerializer

# WE MUST MOVE THIS TO APP CONFIG AND REMOVE IT FROM THE REPO
SECRET = "2f4949c752772e83ec734409da6eb8abe19ffdb6760f9822"
SECURITY_PASSWORD_SALT = "SVExpectoAprobarum2020FAMAF"

manager = LoginManager(SECRET, tokenUrl='/auth/token')


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(SECRET)
    return serializer.dumps(email, salt=SECURITY_PASSWORD_SALT)


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(SECRET)
    try:
        email = serializer.loads(
            token,
            salt=SECURITY_PASSWORD_SALT,
            max_age=expiration
        )
    except:
        return False
    return email


@manager.user_loader
def load_user(user_str, mod=""):  # could also be an asynchronous function
    user = user_str

    with db_session:
        if type(user) is not dict:
            user = User.get(username=user_str)
            if not user:
                user = User.get(email=user_str)
            if user:
                return user.to_dict()
        elif mod != "force":
            user_db = User.get(id=user_str["id"])
            if not user_db.verified:
                return None

    return user
