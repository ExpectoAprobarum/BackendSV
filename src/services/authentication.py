from fastapi_login import LoginManager
from src.models import User
from pony.orm import db_session

SECRET = "2f4949c752772e83ec734409da6eb8abe19ffdb6760f9822"

manager = LoginManager(SECRET, tokenUrl='/auth/token')


@manager.user_loader
def load_user(user_str: str):  # could also be an asynchronous function
    user = user_str

    if type(user) is not dict:
        with db_session:
            user = User.get(username=user_str)
            if not user:
                user = User.get(email=user_str)
            if user:
                return user.to_dict()
    return user
