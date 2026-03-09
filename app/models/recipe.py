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

    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        secondary="recipe_ingredients",
        back_populates="recipe"
    )

    def __repr__(self):
        return f"Recipe(id={self.id}, title={self.title})"