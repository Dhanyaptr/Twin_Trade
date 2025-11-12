from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🧩 Replace with your actual MySQL credentials
SQLALCHEMY_DATABASE_URL = "mysql://root:11May2k4##::@localhost/pairtrade_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
