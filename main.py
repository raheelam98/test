from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated, Optional, List
from sqlmodel import create_engine, SQLModel, select, Field, Session
from jose import jwt, JWTError
from datetime import datetime, timedelta

from pydantic import EmailStr

from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer 

### ============================================================================== ###

class UserModel_13(SQLModel):
    user_email: str
    user_password: str
    user_name: str


class User_13(UserModel_13, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)        

### ============================================================================== ###

DATABASE_URL = 'postgresql://neondb_owner:WC94rhZSjwUe@ep-cool-grass-a5c2gjac-pooler.us-east-2.aws.neon.tech/user_login_db1?sslmode=require'
ALGORITHM = "HS256"
SECRET_KEY = "2e3c44397ddbf3cec54977d1"

from starlette.config import Config
from starlette.datastructures import Secret
from datetime import timedelta

try:
    config = Config(".env")
except FileNotFoundError:
    config = Config()

DATABASE_URL = config("DATABASE_URL", cast=Secret)

# JWT settings
ALGORITHM = config.get("ALGORITHM")
SECRET_KEY = config.get("SECRET_KEY")

ACCESS_TOKEN_EXPIRE_TIME= timedelta(days=int(config.get("ACCESS_TOKEN_EXPIRE_TIME")))

### ============================================================================== ###

connection_string = str(DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)

engine = create_engine(
    connection_string, pool_pre_ping=True, echo=True
)

def get_session():
    with Session(engine) as session:
        yield session

DB_SESSION = Annotated[Session, Depends(get_session)]

async def create_db_and_tables(app: FastAPI):
    print(f'Create Tables ...  {app} ')
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan = create_db_and_tables)

### ============================================================================== ###

app.get('/')
def root_route():
    return 'Authentication & Authorization'

### ============================================================================== ###

def create_access_token(subject: str , expires_delta: timedelta) -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f' to_encode .....  {to_encode}')
    return encoded_jwt

### ============================================================================== ###

def decode_access_token(access_token: str):
    decoded_jwt = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    return decoded_jwt

### ============================================================================== ###
### ============================================================================== ###

def get_users_from_db(session: DB_SESSION):

    users = session.exec(select(User_13)).all() 
    if not users:
        HTTPException(status_code=400, detail="User not found")
    #print('get user fun  ....' )    
    return users 

@app.get('/api/get_users', response_model=list[User_13])
def get_user(session:DB_SESSION):
      user_list = get_users_from_db(session)
      if not user_list:
        raise HTTPException(status_code=404, detail="User Not Found in DB")
      else:
        return user_list

### ============================================================================== ###

def add_user_in_db(form_data: UserModel_13, session: Session):

    user = User_13(**form_data.model_dump())
    #user.user_password = passwordIntoHash(form_data.user_password)

    if not user:
        raise HTTPException(status_code=404, detail="User Not Found")
    
    session.add(user)
    session.commit()
    session.refresh(user)
    print('add user fun  ....', user)
    return user

@app.post("/api/add_user", response_model=User_13)
def add_user(new_user: UserModel_13, session: DB_SESSION):
    # Call the function to add the user to the database
    created_user = add_user_in_db(new_user, session)
    if not created_user:
        raise HTTPException(status_code=404, detail="Can't Add User")
    return created_user

### ============================================================================== ###

@app.post("/login_user_with_token")
def login_user(form_data: UserModel_13, session: DB_SESSION):

    user_name = form_data.user_name
    user_password = form_data.user_password
    user_email = form_data.user_email

    statement = select(User_13).where(
        (User_13.user_name == user_name)and(User_13.user_password == user_password)and(User_13.user_email == user_email))
    
    
    user_in_db = session.exec(statement).one_or_none()
    
    # user_in_db =   session.exec(select(User_9).where(User_9.username == user_name)
    #         and (User_9.password == user_password)).one_or_non
    
    print(f'user_in_db ... {user_in_db}')

    if not user_in_db:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token_expires = timedelta(minutes=30)

    access_token = create_access_token(subject=user_in_db.user_name, expires_delta=access_token_expires)
    
    print(f'access_token ... {access_token}')

    return {"access_token": access_token, "token_type": "bearer", "expires_in": access_token_expires.total_seconds() }

### ============================================================================== ###

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login_with_oauth2_scheme/v1")

### ============================================================================== ###
### ============================================================================== ###

@app.post("/login_with_oauth2_scheme/v1")
def login_v1(form_data: Annotated[OAuth2PasswordRequestForm, Depends(OAuth2PasswordRequestForm)], session: DB_SESSION):

    username = form_data.username
    password = form_data.password

    statement = select(User_13).where(
        (User_13.user_name == username) and (User_13.user_password == password)
    )
    
    user_in_db = session.exec(statement).one_or_none()
    
    print(f'user_in_db ... {user_in_db}')

    if not user_in_db:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(subject=user_in_db.user_name, expires_delta=access_token_expires)
    
    print(f'access_token ... {access_token}')

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": access_token_expires.total_seconds()
    }


### ============================================================================== ###
### ============================================================================== ###

@app.get("/users_with_dependency_injection")
def get_all_users_with_dependency_injection(token:Annotated[str, Depends(oauth2_scheme)] , session: DB_SESSION):  
    print(f'dependency_injection token ... {token} ') 
    user_list = get_users_from_db(session)

    if not user_list:
        raise HTTPException(status_code=404, detail="User Not Found in DB")
    else:
        return user_list
     
### ============================================================================== ###

@app.get("/authorized_special_item")
def get_special_item(token:Annotated[str, Depends(oauth2_scheme)]):
    print(f'get_special_item... ')  
    return {"speical": "items", "token": token}

### ============================================================================== ###

@app.get("/decode_db_specific_user_token")
def read_users_details(token: str):
    user_token_data = decode_access_token(token)

    print(f'decode_user_token_data...  {user_token_data}')  

    return user_token_data

### ============================================================================== ###

@app.get("/decode_db_specific_user_detail")
def read_users_details(token: str, session: Session = Depends(get_session)):
    # Decode the token to extract user data
    user_token_data = decode_access_token(token)

    print(f'user_token_data...  {user_token_data}')

    # Query the database for the user
    statement = select(User_13).where(User_13.user_name == user_token_data["sub"])
    user_in_db = session.exec(statement).first()

    if user_in_db is None:
        raise HTTPException(status_code=404, detail="User not found")

    print(f'user_in_db...  {user_in_db}')

    return user_in_db

### ============================================================================== ###

@app.get("/users/all", response_model=List[UserModel_13])
def get_all_users(session: Session = Depends(get_session)):
    # Query the database to get all users
    statement = select(User_13)
    users_in_db = session.exec(statement).all()

    # Return the list of users without passwords
    return users_in_db

### ============================================================================== ###

@app.get("/get-access-token")
def get_access_token(user_name: str):
    f"""
    Understanding the access token
    -> Takes user_name as input and returns access token
    -> timedelta(minutes=1) is used to set the expiry time of the access token to 1 minute
    """

    access_token_expires = timedelta(minutes=20)
    access_token = create_access_token(
        subject=user_name, expires_delta=access_token_expires)

    return {"access_token": access_token}

### ============================================================================== ###

@app.get("/decode-token")
def decoding_token(access_token: str):
    """
    Understanding the access token decoding and validation
    """
    try:
        decoded_token_data = decode_access_token(access_token)
        return {"decoded_token": decoded_token_data}
    except JWTError as e:
        return {"error": str(e)}

### ============================================================================== ###
### ============================================================================== ###
### ============================================================================== ###
### ============================================================================== ###


# @app.get("/users/all")
# def get_all_users():
#     # Note: We never return passwords in a real application
#     return fake_users_db
    
### ============================================================================== ###
### ============================================================================== ###
### ============================================================================== ###
### ============================================================================== ###
### ============================================================================== ###


### ============================================================================== ###
### ============================================================================== ###
### ============================================================================== ###

### ============================================================================== ###
### ============================================================================== ###
### ============================================================================== ###

