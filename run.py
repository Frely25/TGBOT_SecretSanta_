import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from app.handlers.handlers_to_enter import router_enter
from app.handlers.handlers_to_admin import router_admin
from app.handlers.handlers_to_callback import router_callback

bot = Bot(TOKEN)
dp = Dispatcher()

async def main():
    dp.include_routers(router_enter, router_admin, router_callback)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

