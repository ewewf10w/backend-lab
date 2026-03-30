from typing import Optional, List, Any
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field, field_validator
from models.recipe import Recipe
from models.recipe_ingredient import RecipeIngredient

class RecipeFilter(Filter):
    title__like: Optional[str] = None
    ingredient_id: Any = Field(None)
    
    order_by: List[str] = ["-id"]

    @field_validator("ingredient_id", mode="before")
    @classmethod
    def validate_ingredient_id(cls, v):
        if isinstance(v, str) and v.strip():
            return [int(i.strip()) for i in v.split(",") if i.strip().isdigit()]
        if isinstance(v, int):
            return [v]
        return v
    
    class Constants(Filter.Constants):
        model = Recipe
        ordering_param_name = "sort"

    def filter(self, query):
        current_ingredients = self.ingredient_id
        self.ingredient_id = None
        
        query = super().filter(query)
        
        self.ingredient_id = current_ingredients

        if self.ingredient_id and isinstance(self.ingredient_id, list):
            query = query.join(Recipe.recipe_ingredients).where(
                RecipeIngredient.ingredient_id.in_(self.ingredient_id)
            ).distinct()
        
        return query