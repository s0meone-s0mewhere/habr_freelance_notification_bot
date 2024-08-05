import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import TOKEN, USER_ID, KEYWORDS
from parser import parse_all_pages


dp = Dispatcher()

async def scheduler(bot):
    while True:
        await parse_all_pages(KEYWORDS, bot, USER_ID)
        await asyncio.sleep(60)



async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await asyncio.gather(scheduler(bot), dp.start_polling(bot))
    



if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s %(levelname)s %(message)s")
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped")