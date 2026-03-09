from sqlalchemy import ForeignKey, Column, Integer
from .base import Base

class RecipeAllergen(Base):
    __tablename__ = "recipe_allergens"

    recipe_id = Column(Integer, ForeignKey("recipes.id"), primary_key=True)
    allergen_id = Column(Integer, ForeignKey("allergens.id"), primary_key=True)