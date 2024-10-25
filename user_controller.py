
from fastapi import  HTTPException
from sqlmodel import Session, select

from app.db.db_connector import  DB_SESSION
from app.models.user_model import User, UserModel, UserAuth


### ============================================================================================================= ###

def add_user_in_db(user_form: UserModel, session: Session):
  
    # Convert UserModel to User instance
    #user = User(**user_base.dict())
    user = User(**user_form.model_dump())
   
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    # Add the user to the session
    session.add(user)
    # Commit the session to save the user to the database
    session.commit()
    # Refresh the session to retrieve the new user data, including generated fields like user_id
    session.refresh(user)
    #print('add user fun 2 ....', user)
    return user


### ============================================================================================================= ###

def get_users_from_db(session: DB_SESSION):

    users = session.exec(select(User)).all() 
    if not users:
        HTTPException(status_code=400, detail="User not found")
    #print('get user fun  ....' )    
    return users 