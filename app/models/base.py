import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils import logger

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        logger.info('Attempting to connect to database...')
        engine.connect()
        logger.info('Database connection successful')
    except Exception as e:
        logger.info(f'Database does not exist. Creating database...')
        try:
            db_name = DATABASE_URL.split('/')[-1]
            base_url = DATABASE_URL.rsplit('/', 1)[0]
            
            temp_engine = create_engine(base_url)
            
            with temp_engine.connect() as conn:
                conn.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                conn.commit()
                logger.info(f'Successfully created database: {db_name}')
            
            temp_engine.dispose()
        except Exception as create_error:
            logger.error(f'Failed to create database: {str(create_error)}')
            raise
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info('Successfully created all database tables')
    except Exception as table_error:
        logger.error(f'Failed to create database tables: {str(table_error)}')
        raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()