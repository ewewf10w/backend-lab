from pydantic import BaseModel, Field, ConfigDict
from models.recipe_ingredient import MeasurementEnum
from .cuisines import CuisineRead
from .allergens import AllergenRead
from typing import Optional

class AuthorRead(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RecipeIngredientRead(BaseModel):
    ingredient_id: int
    name: str
    quantity: int
    measurement: MeasurementEnum

    model_config = ConfigDict(from_attributes=True)


class RecipeRead(BaseModel):
    id: int
    title: str
    description: str
    difficulty: int
    cooking_time: int
    cuisine_id: int
    author: Optional[AuthorRead] = None

    cuisine: Optional[CuisineRead] = None
    allergens: Optional[list[AllergenRead]] = None
    ingredients: Optional[list[RecipeIngredientRead]] = Field(None, validation_alias="recipe_ingredients")
    model_config = ConfigDict(from_attributes=True)

