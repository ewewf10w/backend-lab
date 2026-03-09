from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict

from models import db_helper, Cuisine

router = APIRouter(
    tags=["Cuisines"],
    prefix="/cuisines",
)

class CuisineBase(BaseModel):
    name: str

class CuisineCreate(CuisineBase):
    pass

class CuisineRead(CuisineBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

@router.get("", response_model=list[CuisineRead])
async def get_cuisines(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    stmt = select(Cuisine).order_by(Cuisine.id)
    cuisines = await session.scalars(stmt)
    return cuisines.all()

@router.post("", response_model=CuisineRead, status_code=status.HTTP_201_CREATED)
async def create_cuisine(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    cuisine_in: CuisineCreate,
):
    cuisine = Cuisine(**cuisine_in.model_dump())
    session.add(cuisine)
    await session.commit()
    return cuisine

@router.get("/{cuisine_id}", response_model=CuisineRead)
async def get_cuisine(
    cuisine_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    cuisine = await session.get(Cuisine, cuisine_id)
    if not cuisine:
        raise HTTPException(status_code=404, detail="Кухня не найдена")
    return cuisine

@router.patch("/{cuisine_id}", response_model=CuisineRead)
async def update_cuisine(
    cuisine_id: int,
    cuisine_update: CuisineCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    cuisine = await session.get(Cuisine, cuisine_id)
    if not cuisine:
        raise HTTPException(status_code=404, detail="Кухня не найдена")
    
    cuisine.name = cuisine_update.name
    await session.commit()
    return cuisine

@router.delete("/{cuisine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cuisine(
    cuisine_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
):
    cuisine = await session.get(Cuisine, cuisine_id)
    if not cuisine:
        raise HTTPException(status_code=404, detail="Кухня не найдена")
    
    await session.delete(cuisine)
    await session.commit()