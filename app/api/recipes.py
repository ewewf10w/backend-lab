from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from fastapi_filter import FilterDepends
from .filters import RecipeFilter

from config import settings
from models import db_helper, Recipe, User, Ingredient, Allergen, Cuisine, RecipeIngredient
from .cuisines import CuisineRead
from .allergens import AllergenRead
from .ingredients import IngredientRead
from models.recipe_ingredient import MeasurementEnum
from .schemas import RecipeRead, RecipeIngredientRead, AuthorRead
from authentication.fastapi_users import current_active_user

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

class RecipeIngredientCreate(BaseModel):
    ingredient_id: int
    quantity: int
    measurement: MeasurementEnum


class RecipeCreate(RecipeBase):
    allergen_ids: list[int] = Field(default_factory=list)
    ingredients: list[RecipeIngredientCreate] = Field(
        default_factory=list,
        json_schema_extra={
            "example": [{"ingredient_id": 1, "quantity": 100, "measurement": 1}]
        }
    )

class RecipeUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    difficulty: int | None = Field(None, ge=1, le=5)
    cooking_time: int | None = Field(None, gt=0)


@router.get("/read-all/", response_model=list[RecipeRead])
async def get_recipes(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)]
):
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.cuisine),
            joinedload(Recipe.author),
            selectinload(Recipe.allergens),
            selectinload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient)
        )
        .order_by(Recipe.id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

@router.post("/create/", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    recipe_in: RecipeCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    cuisine = await session.get(Cuisine, recipe_in.cuisine_id)
    if not cuisine:
        raise HTTPException(status_code=404, detail="Кухня не найдена")

    recipe_dict = recipe_in.model_dump(exclude={"allergen_ids", "ingredients"})
    recipe = Recipe(**recipe_dict, author_id=user.id)

    if recipe_in.allergen_ids:
        stmt = select(Allergen).where(Allergen.id.in_(recipe_in.allergen_ids))
        res = await session.execute(stmt)
        recipe.allergens = list(res.scalars().all())

    for ing_data in recipe_in.ingredients:
        new_relation = RecipeIngredient(
            ingredient_id=ing_data.ingredient_id,
            quantity=ing_data.quantity,
            measurement=ing_data.measurement
        )
        recipe.recipe_ingredients.append(new_relation)

    session.add(recipe)
    await session.commit()
    
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.cuisine),
            joinedload(Recipe.author),
            selectinload(Recipe.allergens),
            selectinload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient)
        )
        .where(Recipe.id == recipe.id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()

@router.get("/read/{recipe_id}/", response_model=RecipeRead)
async def get_recipe(
    recipe_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)]
):
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient)
        )
        .where(Recipe.id == recipe_id)
    )
    result = await session.execute(stmt)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    return recipe

@router.patch("/update/{recipe_id}/", response_model=RecipeRead)
async def update_recipe(
    recipe_id: int,
    recipe_update: RecipeUpdate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    stmt = (
        select(Recipe)
        .options(
            joinedload(Recipe.cuisine),
            joinedload(Recipe.author),
            selectinload(Recipe.allergens),
            selectinload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient)
        )
        .where(Recipe.id == recipe_id)
    )
    result = await session.execute(stmt)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    
    if recipe.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Вы не можете редактировать чужой рецепт"
        )

    update_data = recipe_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(recipe, key, value)
    
    await session.commit()
    return recipe

@router.delete("/delete/{recipe_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    recipe_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(current_active_user),
):
    recipe = await session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    
    if recipe.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Вы не можете удалить чужой рецепт"
        )
    
    await session.delete(recipe)
    await session.commit()
    return None

@router.get("", response_model=Page[RecipeRead])
async def get_recipes(
    recipe_filter: Annotated[RecipeFilter, FilterDepends(RecipeFilter)],
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    stmt = select(Recipe)
    
    stmt = recipe_filter.filter(stmt)
    stmt = recipe_filter.sort(stmt)
    
    return await apaginate(session, stmt)