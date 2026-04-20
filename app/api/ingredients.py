from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import selectinload, joinedload, attributes

from app.models import db_helper, Ingredient, RecipeIngredient, Recipe
from .schemas import RecipeRead

router = APIRouter(
    tags=["Ingredients"],
    prefix="/ingredients",
)

class IngredientBase(BaseModel):
    name: str

class IngredientCreate(IngredientBase):
    pass

class IngredientRead(IngredientBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


@router.get("", response_model=list[IngredientRead])
async def get_ingredients(session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    stmt = select(Ingredient).order_by(Ingredient.id)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.get("/{ingredient_id}", response_model=IngredientRead)
async def get_ingredient(ingredient_id: int, session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    ingredient = await session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден")
    return ingredient

@router.post("", response_model=IngredientRead, status_code=status.HTTP_201_CREATED)
async def create_ingredient(ingredient_in: IngredientCreate, session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    ingredient = Ingredient(**ingredient_in.model_dump())
    session.add(ingredient)
    await session.commit()
    await session.refresh(ingredient)
    return ingredient

@router.patch("/{ingredient_id}", response_model=IngredientRead)
async def update_ingredient(ingredient_id: int, ingredient_update: IngredientCreate, session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    ingredient = await session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден")
    ingredient.name = ingredient_update.name
    await session.commit()
    return ingredient

@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient(ingredient_id: int, session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    ingredient = await session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден")
    await session.delete(ingredient)
    await session.commit()

@router.get("/{ingredient_id}/recipes")
async def get_recipes_by_ingredient(
    ingredient_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    include: Optional[str] = Query(None, description="(cuisine, allergens, ingredients)"),
    select_fields: Optional[str] = Query(None, alias="select")
):
    ingredient = await session.get(Ingredient, ingredient_id)

    if not ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден")

    stmt = select(Recipe).join(RecipeIngredient).where(
        RecipeIngredient.ingredient_id == ingredient_id
    )

    include_list = [i.strip() for i in include.split(",")] if include else []
    
    if "cuisine" in include_list:
        stmt = stmt.options(joinedload(Recipe.cuisine))
    if "allergens" in include_list:
        stmt = stmt.options(selectinload(Recipe.allergens))
    if "ingredients" in include_list:
        stmt = stmt.options(
            selectinload(Recipe.recipe_ingredients)
            .joinedload(RecipeIngredient.ingredient)
        )

    result = await session.execute(stmt)
    recipes = result.scalars().unique().all()

    response = []

    select_list = [s.strip() for s in select_fields.split(",")] if select_fields else None

    for r in recipes:
        recipe_data = {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "difficulty": r.difficulty,
            "cooking_time": r.cooking_time,
            "cuisine_id": r.cuisine_id
        }

        if "cuisine" in include_list:
            recipe_data["cuisine"] = r.cuisine
        if "allergens" in include_list:
            recipe_data["allergens"] = r.allergens
        if "ingredients" in include_list:
            recipe_data["ingredients"] = [
                {
                    "id": ri.ingredient.id,
                    "name": ri.ingredient.name,
                    "quantity": ri.quantity,
                    "measurement": ri.measurement
                }
                for ri in r.recipe_ingredients
            ]
        
        if select_list:
            filtered_data = {k: v for k, v in recipe_data.items() if k in select_list}
            response.append(filtered_data)
        else:
            response.append(recipe_data)

    return response