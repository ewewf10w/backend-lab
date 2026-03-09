from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload # Не забудь этот импорт для Шага 3

from config import settings
from models import db_helper, Recipe, Ingredient, Allergen, Cuisine

# Импортируем схемы из других файлов роутеров
from .cuisines import CuisineRead
from .allergens import AllergenRead
from .ingredients import IngredientRead

router = APIRouter(
    tags=["Recipes"],
    prefix=settings.url.recipes,
)

class RecipeBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    difficulty: int = Field(..., ge=1, le=5)
    cooking_time: int = Field(..., gt=0)
    cuisine_id: int

class RecipeCreate(RecipeBase):
    allergen_ids: list[int] = []
    ingredient_ids: list[int] = []

class RecipeUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    difficulty: int | None = Field(None, ge=1, le=5)
    cooking_time: int | None = Field(None, gt=0)

class RecipeRead(RecipeBase):
    id: int

    cuisine: CuisineRead | None = None
    allergens: list[AllergenRead] = []
    ingredients: list[IngredientRead] = []
    
    model_config = ConfigDict(from_attributes=True)

@router.get("/read-all/", response_model=list[RecipeRead])
async def get_recipes(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)]
):
    stmt = (
        select(Recipe)
        .options(
            selectinload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.ingredients)
        )
        .order_by(Recipe.id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

@router.post("/create/", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_in: RecipeCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)]
):
    # 1. Проверяем кухню
    cuisine = await session.get(Cuisine, recipe_in.cuisine_id)
    if not cuisine:
        raise HTTPException(status_code=404, detail="Кухня не найдена")

    # 2. Создаем рецепт
    recipe_dict = recipe_in.model_dump(exclude={"allergen_ids", "ingredient_ids"})
    recipe = Recipe(**recipe_dict)

    # 3. Привязываем связи (как и было)
    if recipe_in.allergen_ids:
        stmt = select(Allergen).where(Allergen.id.in_(recipe_in.allergen_ids))
        res = await session.execute(stmt)
        recipe.allergens = list(res.scalars().all())

    if recipe_in.ingredient_ids:
        stmt = select(Ingredient).where(Ingredient.id.in_(recipe_in.ingredient_ids))
        res = await session.execute(stmt)
        recipe.ingredients = list(res.scalars().all())

    session.add(recipe)
    await session.commit()
    
    # --- ВОТ ТУТ ГЛАВНОЕ ИСПРАВЛЕНИЕ ---
    # Перезапрашиваем рецепт со всеми связями, чтобы Pydantic не упал
    stmt = (
        select(Recipe)
        .options(
            selectinload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.ingredients)
        )
        .where(Recipe.id == recipe.id)
    )
    result = await session.execute(stmt)
    recipe_final = result.scalar_one()
    
    return recipe_final

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