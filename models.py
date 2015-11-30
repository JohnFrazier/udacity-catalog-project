from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base


# site users
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(250), nullable=False)


# item categories
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    human_name = "Category"
    uri_path = "category"

    def __repr__(self):
        return "%s %s" % (self.id, self.name)

    def asEditFormData(self):
        return [dict(type="text", db_name="name", value=self.name, human_name="Item Name", editable=True),
                dict(type="text", db_name="id", value=self.id, human_name="ID", editable=False),
                dict(type="hidden", name="requestType", value="edit", editable=False)]

    newFormData = [dict(type="text", db_name="name", human_name="Name")]

    def formUpdate(self, form_data):
        self.name = form_data["name"]


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
    human_name = "Item"
    uri_path = "item"

    def __repr__(self):
        return "".join(["%s, " % s for s in (
            self.id, self.name, self.description, self.category_id)])

    def asEditFormData(self):
        return [dict(type="text", db_name="name", value=self.name, human_name="Item Name", editable=True),
                dict(type="text", db_name="id", value=self.id, human_name="ID", editable=False),
                dict(type="text", db_name="description", value=self.description, human_name="Description", editable=True),
                dict(type="text", db_name="category_id", value=self.category_id, human_name="Category ID", editable=True),
                dict(type="hidden", name="requestType", value="edit", editable=False)]

    newFormData = [dict(type="text", db_name="name", human_name="Name"),
                   dict(type="text", db_name="description", human_name="Description"),
                   dict(type="text", db_name="category_id", human_name="Category ID")]

    def formUpdate(self, form_data):
        self.name = form_data['name']
        self.description = form_data['description']
        self.category_id = form_data["category_id"]
