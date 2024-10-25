
from sqlmodel import create_engine, SQLModel, Session
from fastapi import Depends
from typing import Annotated
from fastapi import FastAPI

#from app.settings import DATABASE_URL

DATABASE_URL = 'postgresql://neondb_owner:WC94rhZSjwUe@ep-cool-grass-a5c2gjac-pooler.us-east-2.aws.neon.tech/user_login_db1?sslmode=require'


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



