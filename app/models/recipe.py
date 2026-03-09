from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    cooking_time: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)

    cuisine_id: Mapped[int] = mapped_column(ForeignKey("cuisines.id"))
    cuisine: Mapped["Cuisine"] = relationship(back_populates="recipes")

    allergens: Mapped[list["Allergen"]] = relationship(
        secondary="recipe_allergens",
        back_populates="recipes"
    )

    # Вспомогательная связь (только для чтения)
    ingredients: Mapped[list["Ingredient"]] = relationship(
        secondary="recipe_ingredients",
        viewonly=True
    )
    
    # Основная рабочая связь для рецептов с граммовками
    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan"
    )