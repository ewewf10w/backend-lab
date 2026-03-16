from typing import Optional, List
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field
from models.recipe import Recipe
from models.recipe_ingredient import RecipeIngredient

class RecipeFilter(Filter):
    title__like: Optional[str] = None
    ingredient_id: Optional[List[int]] = Field(None, alias="ingredient_id")
    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = Recipe
        ordering_param_name = "sort"

    def filter(self, query):
        query = super().filter(query)
        if self.ingredient_id:
            query = query.join(Recipe.recipe_ingredients).where(
                RecipeIngredient.ingredient_id.in_(self.ingredient_id)
            )
        
        return query