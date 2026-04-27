import json
from openai import AsyncOpenAI
from sqlalchemy import select
from app.task_queue import broker
from app.config import settings
from app.models import db_helper, Recipe, Cuisine, Allergen, Ingredient, RecipeIngredient
from app.api.schemas import GeneratedRecipe

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.api.router_key,
)

@broker.task(task_name="generate_recipe_task")
async def generate_recipe_task(prompt: str, user_id: int):
    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b:free", # или та, что выдала 200 OK
        messages=[
            {"role": "system", "content": (
                "You are a professional chef. "
                "All text fields (title, description, cuisine_name, allergen_names, ingredient names) "
                "MUST be in Russian. "
                "Return ONLY pure JSON without markdown."
            )},
            {"role": "user", "content": prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "recipe_schema",
                "schema": GeneratedRecipe.model_json_schema()
            }
        }
    )
    
    content = response.choices[0].message.content
    
    content = content.replace("```json", "").replace("```", "").strip()
    
    try:
        recipe_data = json.loads(content)
        data = GeneratedRecipe.model_validate(recipe_data)
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON. Контент: {content}")
        raise e

    async with db_helper.session_factory() as session:
        stmt_c = select(Cuisine).where(Cuisine.name == data.cuisine_name)
        cuisine = (await session.execute(stmt_c)).scalar_one_or_none()
        if not cuisine:
            cuisine = Cuisine(name=data.cuisine_name)
            session.add(cuisine)

        allergens = []
        for a_name in data.allergen_names:
            stmt_a = select(Allergen).where(Allergen.name == a_name)
            allergen = (await session.execute(stmt_a)).scalar_one_or_none()
            if not allergen:
                allergen = Allergen(name=a_name)
                session.add(allergen)
            allergens.append(allergen)

        # 4. Создание рецепта
        recipe = Recipe(
            title=data.title,
            description=data.description,
            difficulty=data.difficulty,
            cooking_time=data.cooking_time,
            cuisine=cuisine,
            author_id=user_id,
            allergens=allergens
        )
        session.add(recipe)

        for ing in data.ingredients:
            clean_name = ing.name.strip().lower()
            stmt_i = select(Ingredient).where(Ingredient.name == clean_name)
            ingredient = (await session.execute(stmt_i)).scalar_one_or_none()
            if not ingredient:
                ingredient = Ingredient(name=ing.name)
                session.add(ingredient)
            
            rel = RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                quantity=ing.quantity,
                measurement=ing.measurement
            )
            session.add(rel)

        await session.commit()