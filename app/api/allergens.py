from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict

from models import db_helper, Allergen

router = APIRouter(
    tags=["Allergens"],
    prefix="/allergens",
)

class AllergenBase(BaseModel):
    name: str

class AllergenCreate(AllergenBase):
    pass

class AllergenRead(AllergenBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

@router.get("", response_model=list[AllergenRead])
async def get_allergens(session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    stmt = select(Allergen).order_by(Allergen.id)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.get("/{allergen_id}", response_model=AllergenRead)
async def get_allergen(allergen_id: int, session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    allergen = await session.get(Allergen, allergen_id)
    if not allergen:
        raise HTTPException(status_code=404, detail="Аллерген не найден")
    return allergen

@router.post("", response_model=AllergenRead, status_code=status.HTTP_201_CREATED)
async def create_allergen(allergen_in: AllergenCreate, session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    allergen = Allergen(**allergen_in.model_dump())
    session.add(allergen)
    await session.commit()
    await session.refresh(allergen)
    return allergen

@router.patch("/{allergen_id}", response_model=AllergenRead)
async def update_allergen(allergen_id: int, allergen_update: AllergenCreate, session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    allergen = await session.get(Allergen, allergen_id)
    if not allergen:
        raise HTTPException(status_code=404, detail="Аллерген не найден")
    allergen.name = allergen_update.name
    await session.commit()
    return allergen

@router.delete("/{allergen_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allergen(allergen_id: int, session: Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    allergen = await session.get(Allergen, allergen_id)
    if not allergen:
        raise HTTPException(status_code=404, detail="Аллерген не найден")
    await session.delete(allergen)
    await session.commit()