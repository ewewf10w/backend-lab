import json
import logging
from openai import AsyncOpenAI
from sqlalchemy import select

from app.task_queue import broker
from app.config import settings
from app.models import db_helper, Recipe, Cuisine, Allergen, Ingredient, RecipeIngredient
from app.api.schemas import GeneratedRecipe

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.api.router_key,
)

@broker.task(task_name="generate_recipe_task")
async def generate_recipe_task(prompt: str, user_id: int):
    model_id = "deepseek/deepseek-v3.2" 

    system_instructions = (
        "Вы — профессиональный шеф-повар. Ответ должен быть СТРОГО в формате JSON на русском языке. "
        "Правила для поля 'measurement' (используйте только эти строки):\n"
        "- 'GRAMS' для веса и сухих продуктов.\n"
        "- 'PIECES' для штук, зубчиков чеснока или яиц.\n"
        "- 'MILLILITERS' для жидкостей.\n"
        
        "Поле quantity всегда должно быть больше 0. Не добавляйте лишний текст или разметку markdown.\n"
        "ЗАПРЕЩЕНО использовать цифры 1, 2, 3 в поле measurement. Только СЛОВА.\n"
        "Рецепт должен быть обязательно на Русском языке\n"
    )

    response = await client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system_instructions},
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

    if not response.choices or not response.choices[0].message.content:
        logger.error("API вернуло пустой ответ")
        return

    raw_content = response.choices[0].message.content
    clean_content = raw_content.replace("```json", "").replace("```", "").strip()

    try:
        recipe_data = json.loads(clean_content)
        data = GeneratedRecipe.model_validate(recipe_data)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Ошибка валидации данных: {e}. Контент: {clean_content}")
        raise e

    async with db_helper.session_factory() as session:
        c_name = data.cuisine_name.strip().capitalize()
        stmt_c = select(Cuisine).where(Cuisine.name == c_name)
        cuisine = (await session.execute(stmt_c)).scalar_one_or_none()
        if not cuisine:
            cuisine = Cuisine(name=c_name)
            session.add(cuisine)

        allergens = []
        for a_name in data.allergen_names:
            a_name_clean = a_name.strip().lower()
            stmt_a = select(Allergen).where(Allergen.name == a_name_clean)
            allergen = (await session.execute(stmt_a)).scalar_one_or_none()
            if not allergen:
                allergen = Allergen(name=a_name_clean)
                session.add(allergen)
            allergens.append(allergen)

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
            i_name_clean = ing.name.strip().lower()
            stmt_i = select(Ingredient).where(Ingredient.name == i_name_clean)
            ingredient = (await session.execute(stmt_i)).scalar_one_or_none()
            if not ingredient:
                ingredient = Ingredient(name=i_name_clean)
                session.add(ingredient)
            
            valid_quantity = ing.quantity if ing.quantity > 0 else 1
            
            rel = RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                quantity=valid_quantity,
                measurement=ing.measurement
            )
            session.add(rel)

        await session.commit()
        logger.info(f"Рецепт '{data.title}' успешно сохранен.")