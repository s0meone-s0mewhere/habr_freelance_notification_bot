import aiohttp
import logging
import bs4
import asyncio
from dataclasses import dataclass
from typing import List
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


async def get_page(keyword: str, type: str = 'list_of_tasks'):
    async with aiohttp.ClientSession() as session:
        if type == "list_of_tasks":
            async with session.get(f"https://freelance.habr.com/tasks?q={keyword}") as response:
                return await response.text()
        elif type == "specific_task":
            async with session.get(f"https://freelance.habr.com{keyword}") as response:
                return await response.text()


@dataclass
class Task:
    title: str
    description: str
    price: str
    tags: list
    link: str 



scanned_tasks = set()
last_task = {}

def parse_description(soup):
    for br in soup.find_all('br'):
        br.replace_with('\n')

    for p in soup.find_all('p'):
        p.insert_before('\n') 
        p.insert_after('\n')

    return soup.get_text()[:3500]


async def parser(task, title, link):
    get_task_page = asyncio.create_task(get_page(title.contents[0].get("href"), type="specific_task"))
    title_text = title.text
    task_page = await get_task_page 
    parse_only_description = bs4.SoupStrainer("div", class_="task__description")
    soup = bs4.BeautifulSoup(task_page, "lxml", parse_only=parse_only_description).div
    description = parse_description(soup)
    price = task.find("div", class_="task__price").text
    tags = [tag.text for tag in task.find_all("a", class_="tags__item_link")]
    parsed_task = Task(title_text, description, price, tags, link)
    return parsed_task

async def page_parser(keyword: str):
    page = await get_page(keyword)
    parse_only_tasks = bs4.SoupStrainer("ul", id="tasks_list")
    soup = bs4.BeautifulSoup(page, "lxml", parse_only=parse_only_tasks)
    tasks = soup.find_all("article", class_="task task_list")
    parsed_tasks: List[Task] = []
    
    for index, task in enumerate(tasks):
        title = task.find("div", class_="task__title")
        link = f"https://freelance.habr.com{title.contents[0].get("href")}"

        if link != last_task.get(keyword):
            if link not in scanned_tasks:
                scanned_tasks.add(link)
                if not last_task.get(keyword):
                    parsed_task = await parser(task, title, link)
                    parsed_tasks.append(parsed_task)
                    last_task[keyword] = link
                    return parsed_tasks
                
            if index == 0:
                last_task[keyword] = link
        else:
            logging.info("else block, there are no new tasks")
            break
        logging.info("tasks parsed")
    return parsed_tasks

async def parse_all_pages(keywords, bot, user_id):
    for keyword in keywords:
        result = await page_parser(keyword)
        if result:
            for i in result:
                message = f"{i.title} \n\nОписание: {i.description} \n\nЦена: {i.price} \n\nТэги: {', '.join(i.tags)}"
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text="Ссылка на заказ",
                    url=f"{i.link}")
                )
                await bot.send_message(chat_id=user_id, text=message, reply_markup=builder.as_markup())


async def test():
     from config import KEYWORDS
     for keyword in KEYWORDS:
        result = await page_parser(keyword)
        if result:
            for i in result:
                message = f"{i.title} \n\nОписание: {i.description} \n\nЦена: {i.price} \n\nТэги: {', '.join(i.tags)}"
                print(message)


async def main():
    await test()


if __name__ == '__main__':
    asyncio.run(main())