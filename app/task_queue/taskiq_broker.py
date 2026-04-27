from asyncio import sleep

from taskiq import SimpleRetryMiddleware, TaskiqMessage, TaskiqMiddleware, TaskiqResult
import taskiq_fastapi
from taskiq_aio_pika import AioPikaBroker


class CatchErrorMiddleware(TaskiqMiddleware):
    async def on_error(
        self,
        message: TaskiqMessage,
        result: TaskiqResult,
        exception: BaseException,
    ) -> None:

        # max_retries = message.labels.get("_retries")
        print("***********************************************")
        # await sleep(5000)
        print(message.labels)
        # save to databse
        error = str(exception)
        print(error)


broker = AioPikaBroker(
    url="amqp://guest:guest@localhost:5672//",
).with_middlewares(SimpleRetryMiddleware(default_retry_count=2), CatchErrorMiddleware())

taskiq_fastapi.init(broker, "app.main:main_app")
