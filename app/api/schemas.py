from pydantic import BaseModel, Field, ConfigDict
from models.recipe_ingredient import MeasurementEnum
from .cuisines import CuisineRead
from .allergens import AllergenRead


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

    cuisine: CuisineRead | None = None
    allergens: list[AllergenRead] = []

    ingredients: list[RecipeIngredientRead] = Field(validation_alias="recipe_ingredients")

    model_config = ConfigDict(from_attributes=True)