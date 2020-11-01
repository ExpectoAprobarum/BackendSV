from fastapi import FastAPI
from fastapi_login import LoginManager
from src.models import User
from pony.orm import db_session, commit


SECRET = "2f4949c752772e83ec734409da6eb8abe19ffdb6760f9822"

manager = LoginManager(SECRET, tokenUrl='/auth/token')

@manager.user_loader
def load_user(userStr: str):  # could also be an asynchronous function
    user = userStr

    if type(user) is not dict:    
        with db_session:
            user = User.get(username=userStr)
            if not user:
                user = User.get(email=userStr)
            if user:
                return user.to_dict()

    return user