from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


def init_db(db_path):
    from models import User, Category, Item
    engine = create_engine(db_path)
    DBSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return (engine, DBSession)
