from fastapi import (
    APIRouter,
    Query,
    Path,
    Form,
    File,
    UploadFile
)
from config import settings
from pydantic import BaseModel, Field
from typing import Annotated, Literal
from fastapi.responses import HTMLResponse
import shutil
from pathlib import Path as SysPath

router = APIRouter(
    tags=["Examples"],
    prefix=settings.url.examples,
)
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float

@router.post("/body-example/")
async def create_item(item: Item):
    return item

@router.get("/query-validation/")
async def read_items(q: Annotated[str | None, Query(max_length=50)] = None):
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results

@router.get("/items/{item_id}")
async def read_items(
    item_id: Annotated[int, Path(title="The ID of the item to get")],
    q: Annotated[str | None, Query(alias="item-query")] = None,
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results

class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

@router.get("/query-model/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query

class Ingredient(BaseModel):
    name: str
    quantity: float


class RecipeNested(BaseModel):
    title: str
    ingredients: list[Ingredient]

@router.post("/nested-model")
async def create_nested_recipe(recipe: RecipeNested):
    return recipe

@router.post("/form-example/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}

class FormData(BaseModel):
    username: str
    password: str

@router.post("/form-model/")
async def login(data: Annotated[FormData, Form()]):
    return data

@router.get("/response-format")
async def response_format(format: str ):
    if format == "json":
        return {"message": "JSON"}

    elif format == "html":
        return HTMLResponse("<h1>HTML</h1>")

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    allowed_types = ["image/png", "image/jpeg", "image/webp"]

    if file.content_type not in allowed_types:
        return {"error": "Unsupported file type"}

    file_location = SysPath("app/static/images") / file.filename
    file_location.parent.mkdir(parents=True, exist_ok=True)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"url": f"/static/images/{file.filename}"}
    