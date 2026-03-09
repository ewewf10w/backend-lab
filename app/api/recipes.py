from fastapi import (
    APIRouter, Depends, status, HTTPException
)
from config import settings
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from models import db_helper, Recipe

router = APIRouter(
    tags=["Recipes"],
    prefix=settings.url.recipes,
)

class RecipeBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    
    difficulty: int = Field(..., ge=1, le=5)
    cooking_time: int = Field(..., gt=0)

class RecipeCreate(RecipeBase):
    pass

class RecipeUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    difficulty: int | None = Field(None, ge=1, le=5)
    cooking_time: int | None = Field(None, gt=0)

class RecipeRead(RecipeBase):
    id: int

    class Config:
        from_attributes = True

@router.get("/read-all/", response_model=list[RecipeRead])
async def get_recipes(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)]
):
    stmt = select(Recipe).order_by(Recipe.id)
    recipes = await session.scalars(stmt)
    return recipes.all()

@router.post("/create/", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_in: RecipeCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)]
):
    recipe = Recipe(**recipe_in.model_dump())
    session.add(recipe)
    await session.commit()
    return recipe

@router.get("/read/{recipe_id}/", response_model=RecipeRead)
async def get_recipe(
    recipe_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)]
):
    recipe = await session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    return recipe

@router.patch("/update/{recipe_id}/", response_model=RecipeRead)
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)]
):
    recipe = await session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    update_data = recipe_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(recipe, key, value)
    
    await session.commit()
    return recipe

@router.delete("/delete/{recipe_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)]
):
    recipe = await session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    
    await session.delete(recipe)
    await session.commit()
    return None