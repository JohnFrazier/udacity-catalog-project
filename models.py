from sqlalchemy import Column, ForeignKey, Integer, String, desc, DateTime
from sqlalchemy.orm import relationship, backref
from database import Base
from datetime import datetime


# site users
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    provider = Column(String(250))
    fb_id = Column(String(250))

    def as_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            provider=self.provider)


# items within the category
class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    category = relationship("Category", backref=backref("items"))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship(User, backref=backref("items"))
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    image = relationship("Image", backref=backref('images'))
    updated_date = Column(DateTime, default=datetime.utcnow)
    created_date = Column(DateTime, default=datetime.utcnow)

    def as_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            description=self.description,
            category_id=self.category_id,
            category=self.category)


# item categories
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)

    def as_dict(self):
        return dict(id=self.id, name=self.name)


# image data
class Image(Base):
    __tablename__ = 'images'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    original_name = Column(String(80), nullable=False)
    filename = Column(String(80), nullable=False)

    def as_dict(self):
        return dict(
            id=self.id,
            user_id=self.user_id,
            original_name=self.original_name,
            filename=self.filename)
