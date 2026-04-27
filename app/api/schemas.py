from pydantic import BaseModel, Field, ConfigDict
from app.models.recipe_ingredient import MeasurementEnum
from .cuisines import CuisineRead
from .allergens import AllergenRead
from typing import Optional, List

class AuthorRead(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RecipeIngredientRead(BaseModel):
    ingredient_id: int
    name: str
    quantity: float
    measurement: MeasurementEnum

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


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


class GeneratedIngredient(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    name: str = Field(..., description="Название ингредиента на русском языке")
    quantity: float = Field(..., description="Количество (целое число), не может быть равно 0")
    measurement: MeasurementEnum = Field(
        ..., 
        description="Единица измерения. Используй ТОЛЬКО: GRAMS, PIECES или MILLILITERS"
    )

class GeneratedRecipe(BaseModel):
    title: str = Field(..., description="Название рецепта на русском языке")
    description: str = Field(..., description="Описание на русском языке")
    difficulty: int
    cooking_time: int
    cuisine_name: str = Field(..., description="Название кухни на русском языке (например: Итальянская, Японская)")
    allergen_names: List[str] = Field(..., description="Список аллергенов на русском языке")
    ingredients: List[GeneratedIngredient]