from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import selectinload, joinedload

from models import db_helper, Ingredient, RecipeIngredient
from .recipes import RecipeRead

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

@router.get("/{ingredient_id}/recipes/", response_model=list[RecipeRead])
async def get_recipes_by_ingredient(
    ingredient_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)]
):
    ingredient = await session.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ингредиент не найден")

    stmt = (
        select(Recipe)
        .join(Recipe.recipe_ingredients)
        .where(RecipeIngredient.ingredient_id == ingredient_id)
        .options(
            selectinload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient)
        )
    )

    result = await session.execute(stmt)
    recipes = result.scalars().all()

    return recipes