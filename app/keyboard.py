import sqlite3
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                            InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Войти в комнату", callback_data="enter")],
    [InlineKeyboardButton(text="Создать комнату", callback_data="create")]
])
"""

names = ["Вася", "Катя", "Федя", "Антон"]

async def inline_names():
    keyboard = InlineKeyboardBuilder()
    for name in names:
        keyboard.add(InlineKeyboardButton(text=name, callback_data=f"{name}"))
    return keyboard.adjust(2).as_markup()

"""

async def btns_rooms(name: str):
    keyboard, ret_list = InlineKeyboardBuilder(), ""

    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM rooms WHERE name=?", (name,))
        filtered_list = cursor.fetchall()
        
        
        for room in filtered_list:
            btn = f"Название: {room[1]} | ID: {room[0]}"
            keyboard.add(InlineKeyboardButton(text=btn, callback_data=btn))
            ret_list += f"{btn};"
    return keyboard.adjust(2).as_markup(), len(filtered_list), ret_list[:-1]

async def btns_list_members(id: int):
    keyboard = InlineKeyboardBuilder()
    # 754757645 пвапвыа
    # 3452634256 ывапваырвыао
    # 2342342 ывапывапы
    # 8656856 ывапывапвыапыва
    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT users FROM rooms WHERE id=?", (id,))
        data = cursor.fetchone()[0]
        if (data == None):
            keyboard.add(InlineKeyboardButton(text="Выйти в меню комнаты", callback_data="menu_room"))
            return keyboard.as_markup(), 0
        data = [int(x) for x in (data.split(";"))]
        voprosiki = ','.join(["?"] * len(data))
        
        cursor.execute(f"SELECT * FROM users WHERE id IN ({voprosiki})", (data))
        get_bd = cursor.fetchall()
        for user in get_bd:
            keyboard.add(InlineKeyboardButton(text=f"{user[1]}", callback_data=f"{user[0]}"))
        keyboard.add(InlineKeyboardButton(text="Выйти в меню комнаты", callback_data="menu_room"))
        return keyboard.adjust(2).as_markup(), 1


menu_to_rooms_for_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Игра", callback_data="menu_play")],
        [InlineKeyboardButton(text="Список участников", callback_data="list_of_members"), InlineKeyboardButton(text="Пригласить", callback_data="send_invite")],
        [InlineKeyboardButton(text="Информация о комнате", callback_data="info_of_room")],
        [InlineKeyboardButton(text="Выход в главное меню", callback_data="main_menu")]
    ]
)

menu_to_rooms_for_player = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Список участников", callback_data="list_of_members")],
    [InlineKeyboardButton(text="Выход в главное меню", callback_data="main_menu")]
])

menu_for_info_of_room = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Сменить пароль")],
    [KeyboardButton(text="Сменить название")],
    [KeyboardButton(text="Выход в главное меню")]
])

menu_for_member = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Сделать админом", callback_data="up_member")],
    [InlineKeyboardButton(text="Выгнать", callback_data="kick_member")], 
    [InlineKeyboardButton(text="Назад", callback_data="back")]
])

