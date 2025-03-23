import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from data_base.db import Database
from config import Config
from time_to_deadline import *

config = Config()
BOT_TOKEN = config.BOT_TOKEN
DATABASE_URL = config.DATABASE_URL

logging.basicConfig(level=logging.INFO)
bot = Bot(BOT_TOKEN)
db = Database(DATABASE_URL, db_name=config.DATABASE_NAME)
db.check_connection()
storage = MemoryStorage()
dp = Dispatcher()

class TaskState(StatesGroup):
    task_text = State()
    deadline = State()

class TaskEditState(StatesGroup):
    task_id = State()
    new_text = State()
    new_deadline = State()

class TaskDeleteState(StatesGroup):
    task_id = State()
    new_text = State()
    deadline_delete = State()

@dp.message(Command('start', 'help'))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот для планирования задач.\n"
                        "Доступные команды:\n"
                        "/add - Добавить задачу\n"
                        "/list - Показать список задач\n"
                        "/edit - Редактировать задачу\n"
                        "/delete_by_date - Удалить задачу(и) на определённую дату\n"
                        "/help - Показать это сообщение\n"
                        "/clear_tasks - Удалить все задачи\n")

@dp.message(Command('add'))
async def add_task(message: types.Message, state: FSMContext):
    await state.set_state(TaskState.task_text)
    await message.reply('Введите текст задачи:')

@dp.message(TaskState.task_text)
async def process_task_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['task_text'] = message.text
    await state.set_data(data)
    await state.set_state(TaskState.deadline)
    await message.reply('Отлично! Теперь установите дедлайн в формате ДД-ММ-ГГГГ')

@dp.message(TaskState.deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    try:
        deadline = datetime.strptime(message.text, '%d-%m-%Y')
        data = await state.get_data()
        task_text = data['task_text']
        db.add_task(task_text, message.text)
        await state.clear()
        await message.reply('Задача успешно добавлена')
    except ValueError:
        await message.reply('Неверный формат даты. Пожалуйста, используйте формат ДД-ММ-ГГГГ.')

@dp.message(Command('list'))
async def list_tasks(message: types.Message):
    tasks = db.get_all_task()
    if tasks:
        response = 'Список задач:\n\n'
        for i, task in enumerate(tasks, start=1):
            if 'id' in task and 'task_text' in task and 'deadline' in task:
                deadline = datetime.strptime(task['deadline'], '%d-%m-%Y')
                if deadline < datetime.now():
                    status = 'Просрочено'
                else:
                    days, hours, minutes, seconds = calculate_time_left(task['deadline'])
                    status = f'Осталось: {format_time_left(days, hours, minutes, seconds)}'
                response += f'{i}. {task["task_text"]} (Дедлайн: **{task["deadline"]}**, {status})\n\n'
            else:
                response += f'- Задача без ID или текста\n'
        await message.reply(response, parse_mode="Markdown")
    else:
        await message.reply('Список задач пуст. Добавьте задачу с помощью команды /add')


@dp.message(Command('edit'))
async def edit_task(message: types.Message, state: FSMContext):
    tasks = db.get_all_task()
    if tasks:
        response = 'Список задач для редактирования:\n'
        for i, task in enumerate(tasks, start=1):
            if 'id' in task and 'task_text' in task and 'deadline' in task:
                deadline = datetime.strptime(task['deadline'], '%d-%m-%Y')
                if deadline < datetime.now():
                    status = 'Просрочено'
                else:
                    time_left = calculate_time_left(task['deadline'])
                    days, hours, minutes, seconds = time_left
                    status = f'Осталось: {format_time_left(days, hours, minutes, seconds)}'
                response += f'{i}. {task["task_text"]} (Дедлайн: {task["deadline"]}, {status})\n'
            else:
                response += f'- Задача без ID или текста\n'
        await state.set_state(TaskEditState.task_id)
        await message.reply(response + "\nВведите номер задачи для редактирования:")
    else:
        await message.reply('Список задач пуст. Добавьте задачу с помощью команды /add')
        await state.clear()

@dp.message(TaskEditState.task_id)
async def process_task_id(message: types.Message, state: FSMContext):
    try:
        task_number = int(message.text)
        tasks = db.get_all_task()
        if task_number > 0 and task_number <= len(tasks):
            task_id = tasks[task_number - 1]['id']
            await state.update_data(task_id=task_id)
            await state.set_state(TaskEditState.new_text)
            await message.reply("Теперь введите новый текст задачи (или нажмите /skip, чтобы пропустить):")
        else:
            await message.reply("Номер задачи неверный.")
            await state.clear()
    except ValueError:
        await message.reply("Неверный формат ввода. Введите номер задачи.")
        await state.reset_state()

@dp.message(TaskEditState.new_text)
async def process_new_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['new_text'] = message.text
    await state.update_data(data)
    await state.set_state(TaskEditState.new_deadline)
    await message.reply("Отлично! Теперь введите новый дедлайн (или /skip, чтобы пропустить):")

@dp.message(TaskEditState.new_text, Command("skip"))
async def skip_new_text(message: types.Message, state: FSMContext):
    await state.set_state(TaskEditState.new_deadline)
    await message.reply("Пропускаем изменение текста. Теперь введите новый дедлайн (или /skip, чтобы пропустить):")

@dp.message(TaskEditState.new_deadline)
async def process_new_deadline(message: types.Message, state: FSMContext):
    try:
        new_deadline = message.text
        data = await state.get_data()
        task_id = data['task_id']
        new_text = data.get('new_text')
        db.edit_task(task_id, new_text=new_text, new_deadline=new_deadline)
        await state.clear()
        await message.reply("Задача успешно отредактирована!")
    except ValueError:
        await message.reply("Неверный формат даты. Пожалуйста, используйте формат ДД-ММ-ГГГГ.")
        await state.reset_state()

@dp.message(TaskEditState.new_deadline, Command("skip"))
async def skip_new_deadline(message: types.Message, state: FSMContext):
    data = await state.get_data()
    task_id = data['task_id']
    new_text = data.get('new_text')
    db.edit_task(task_id, new_text=new_text)
    await state.clear()
    await message.reply("Задача успешно отредактирована (дедлайн оставлен без изменений)!")


@dp.message(Command('delete_by_date'))
async def delete_by_date(message: types.Message, state: FSMContext):
    await state.set_state(TaskDeleteState.deadline_delete)
    await message.reply("Введите дату для удаления задач (в формате ДД-ММ-ГГГГ):")

@dp.message(TaskDeleteState.deadline_delete)
async def process_delete_date(message: types.Message, state: FSMContext):
    date = message.text
    try:
        deleted_count = db.delete_tasks_by_date(date)

        if deleted_count is None:  # Handle the case where deleted_count is None
            deleted_count = 0      # Set it to 0 so the comparison works

        if deleted_count > 0:
            await state.clear()
            await message.reply("Задачи на эту дату успешно удалены!")
        else:
            await state.clear()
            await message.reply("На эту дату нет запланированных задач.")

    except Exception as e:
        await message.reply(f"Ошибка удаления задач: {e}")
        await state.clear()

@dp.message(Command('clear_tasks'))
async def clear_tasks(message: types.Message):
    db.delete_all_tasks()
    await message.reply("Все задачи успешно удалены!")

async def main():
    await dp.start_polling(bot, skip_updates=True, storage=storage)

if __name__ == '__main__':
    asyncio.run(main())