from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from .base import Base

class Allergen(Base):
    __tablename__ = "allergens"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    def __repr__(self):
        return f"Allergen(id={self.id}, name={self.name})"