import sqlite3
import re
import asyncio
import app.keyboard as kb
import app.states as sts

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router_admin = Router()

@router_admin.message(sts.InRoomToAdmin.new_password)
async def handler_to_old_password(message: Message, state: FSMContext):
    pattern = r"[a-zA-Z0-9]{8,20}"
    match = re.search(pattern, message.text)

    if (match != None):
        data = await state.get_data()
        with sqlite3.connect("secret_santa.db") as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE rooms SET password = ? WHERE id = ?", (message.text, int(data['main_menu'])))
            conn.commit()
        await message.answer("Все прошло успешно, вы сменили пароль! Выберете, что будете делать дальше",
                             reply_markup=kb.menu_for_info_of_room)
        await state.set_state(sts.InRoomToAdmin.info_of_room)
    elif message.text.strip() == "0":
        await message.answer("Окей, раз передумал, то не напрягаю.", reply_markup=kb.menu_for_info_of_room)
        await state.set_state(sts.InRoomToAdmin.info_of_room)
    else:
        await message.answer("""Новый пароль не подходит под критерии:
    -8 символов
    -Латинские буквы или цифры""") 


@router_admin.message(sts.InRoomToAdmin.old_password)
async def handler_to_old_password(message: Message, state: FSMContext):
    data = await state.get_data()
    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM rooms WHERE id=?", (int(data['main_menu']), ))
        get_bd = cursor.fetchone() 
        if get_bd[0] == message.text:
            await message.answer("Отлично! Введите новый пароль, если хотите отменить смену пароля -> введите 0.")
            await state.set_state(sts.InRoomToAdmin.new_password)
        elif message.text == "0":
            await message.answer("Окей, раз передумал, то не напрягаю.", reply_markup=kb.menu_for_info_of_room)
            await state.set_state(sts.InRoomToAdmin.info_of_room)
        else:
            await message.answer("Вы ввели неверный пароль!")
    
@router_admin.message(sts.InRoomToAdmin.name_room)
async def handler_to_new_name(message: Message, state:FSMContext):
    data = await state.get_data()
    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM rooms WHERE id=?", (int(data['main_menu']), ))
        get_bd = cursor.fetchone() 
        if get_bd[0] == message.text:
            await message.answer("Вы ввели уже существующее название")
        elif message.text.strip() == "0":
            await message.answer("Окей, раз передумал, то не напрягаю.", reply_markup=kb.menu_for_info_of_room)
            await state.set_state(sts.InRoomToAdmin.info_of_room)
        else:
            cursor.execute("UPDATE rooms SET name = ? WHERE id = ?", (message.text, int(data['main_menu'])))
            conn.commit()
            await message.answer("Все прошло успешно, вы сменили название! Выберете, что будете делать дальше",
                                reply_markup=kb.menu_for_info_of_room)
            await state.set_state(sts.InRoomToAdmin.info_of_room)

@router_admin.message(sts.InRoomToAdmin.send_invite_name)
async def send_invite_stage_name(message: Message, state: FSMContext):
    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name = ?", (message.text, ))
        get_bd = cursor.fetchall()
        if get_bd == None:
            await message.answer(f"Пользователь с ником {message.text} не зарегестрирован в боте")
        elif len(get_bd) == 1:
            info = await state.get_data()
            info = info["main_menu"]
            cursor.execute("SELECT * FROM rooms WHERE id = ?", (int(info), ))
            info = cursor.fetchone()[0]
            print(f"info: {info}")
            print(f"get_bd: {get_bd}")
            await message.bot.send_message(chat_id=int(get_bd[0][0]), text=f"Пользователь {message.chat.first_name} отправил вам предложение вступить в комнату", reply_markup=kb.menu_to_invited)
            await message.answer(f"Приглашение пользователю <b>{message.text}</b> отправлено", parse_mode="html")
        else:
            keyboard, users_str = await kb.btns_to_people(message.text)
            await state.update_data(send_invite_name=users_str)
            await message.answer(f"В базе данных есть несколько пользователей с именем <b>{message.chat.first_name}</b>. Вы берете нужного вам пользователя по chat_id.", reply_markup=keyboard, parse_mode="html")

@router_admin.message(sts.InRoomToAdmin.info_of_room)
async def handler_to_info(message: Message, state: FSMContext):
    text = message.text.lower()
    if text == "сменить пароль":
        await state.set_state(sts.InRoomToAdmin.old_password)
        await message.answer("Чтобы сменить пароль, сначала введите старый! Или введите 0, чтобы отменить свой выбор")
    elif text == "cменить название":
        await state.set_state(sts.InRoomToAdmin.name_room)
        await message.answer("Введите новое название комнаты! Или введите 0, чтобы отменить свой выбор")
    elif text == "выход в главное меню":
        await state.set_state(sts.InRoomToAdmin.main_menu)
        await message.answer(f"Вы находитесь в главном меню вашей команты.", reply_markup=kb.menu_to_rooms_for_admin)
