from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base


# site users
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    provider = Column(String(250))
    fb_id = Column(String(250))


# item categories
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)


# items within the category
class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category_relationship = relationship(Category)
    user_id = Column(Integer, ForeignKey('users.id'))
    user_relationship = relationship(User)
