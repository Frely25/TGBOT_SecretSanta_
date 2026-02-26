import re 
import sqlite3

import app.keyboard as kb
import app.states as sts 


from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


router_enter = Router()

@router_enter.message(CommandStart())
async def cmd_start(message: Message):
    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS users 
                                (id TEXT PRIMARY KEY, 
                                name TEXT)
        """)
        cursor.execute("""CREATE TABLE IF NOT EXISTS rooms
                                (id INT PRIMARY KEY, 
                                name TEXT,
                                password TEXT, 
                                id_admin TEXT, 
                                users TEXT)
        """)
        cursor.execute("SELECT id FROM users WHERE id=?", (message.chat.id, ))
        if cursor.fetchone() == None:
            print("Такого пользователя не существует")
            data = (message.chat.id, message.from_user.first_name)
            cursor.execute("INSERT INTO users (id, name) VALUES (?,?)", data)
            conn.commit()
    await message.answer(f"Добро пожаловать, {message.from_user.first_name},в игру \"Тайный санта в тгэшке\".\nВыберете пункт меню:", reply_markup=kb.main)


"""     Состояния входа в комнату       """


#Отловка сообщения пользователя в статусе написания НАЗВАНИЯ комнаты при входе
@router_enter.message(sts.EnterRoom.name_for_enter)
async def stage_first_enter(message: Message, state: FSMContext):
    btns = await kb.btns_rooms(message.text)
    match btns[1]:
        case 0:
            await message.answer("Вы ввели не существующую комнату. Введите другое название!")
        case 1:
            await state.update_data(name_for_enter=btns[2])
            await state.set_state(EnterRoom.password_for_enter)
            await message.answer(f"Отлично! Теперь введите пароль для комнаты \"{message.text}\":")
        case _:
            #await state.set_state(EnterRoom.save_btns)
            await state.update_data(name_for_enter=btns[2])
            await message.answer("По вашему запросу подходит несколько комнат. Выберете комнату с нужным для вас ID."
                                        , reply_markup= btns[0])

@router_enter.message(sts.EnterRoom.password_for_enter)
async def stage_second_enter(message: Message, state: FSMContext):
    data = await state.get_data()
    data = str(data['name_for_enter'])
    id, name = int(data[data.index('|')+6 : ]), data[data.index(' ')+1 : data.index('|')-1]
    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password, id_admin  FROM rooms WHERE id=?", (id, )) #Вытянуть ID при после ввода названия и распределения
        answer = cursor.fetchone()
        data = await state.get_data()
        if answer[0] == message.text:
            await message.answer(f"Вы успешно вошли в комнату <b>{name}</b>", parse_mode="html")
            if str(message.chat.id) == answer[1]:
                await state.set_state(sts.InRoomToAdmin.main_menu)
                await state.update_data(main_menu=id)
                await message.answer(f"Вы находитесь в главном меню вашей команты.", reply_markup=kb.menu_to_rooms_for_admin)
            else:
                #UPDATE products SET product_name = CONCAT(product_name, '-new') WHERE id = 42
                await state.set_state(InRoomToPlayer.main_menu)
                await state.update_data(main_menu=id)
                cursor.execute("SELECT users FROM rooms WHERE id = ?", (id, ))
                get_bd = cursor.fetchone()[0]
                print(f"get_bd: {get_bd}")
                get_bd = f'{get_bd};?' if get_bd != None else '?'
                print(f"get_bd after: {get_bd}")
                if get_bd == "?" or not(str(message.chat.id) in get_bd.split(';')):
                    cursor.execute(f"UPDATE rooms SET users = {get_bd} WHERE id=?", (f"{message.chat.id}", id))
                    conn.commit()
                await message.answer(f"Вы находитесь в главном меню {name} команты.", reply_markup=kb.menu_to_rooms_for_player)



"""     Состояния создания комнат      """

#Отловка сообщения пользователя в статусе написания НАЗВАНИЯ комнаты
@router_enter.message(sts.CreateRoom.name)
async def stage_first(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(CreateRoom.password)
    await message.answer("Отлично! Теперь придумайте пароль для вашей комнаты!")


#Отловка сообщения пользователя в статусе написания ПАРОЛЯ для комнаты
@router_enter.message(sts.CreateRoom.password)
async def stage_second(message:Message, state: FSMContext):

    pattern = r"[a-zA-Z0-9]{8,20}"
    match = re.search(pattern, message.text)
    if (match != None):
        with sqlite3.connect("secret_santa.db") as conn:
            cursor = conn.cursor()
            save_data = ""
            await state.update_data(password=message.text)
            data = await state.get_data()
            await message.answer(f"Вы успешно создали комнату!\nНазвание: {data['name']}\nПароль: {data['password']}")
            cursor.execute("SELECT id FROM rooms ORDER BY id")
            created_rooms = cursor.fetchall()
            flag = True
            for i in range(len(created_rooms) - 1):
                if created_rooms[i][0] + 1 != created_rooms[i + 1][0]:
                    cursor.execute("INSERT INTO rooms (id, name, password) VALUES (?, ?, ?)"
                                    ,(created_rooms[i][0]+1, data["name"], data["password"])
                    )
                    save_data = f"{created_rooms[i][0]+1}"
                    flag = False
                    break
            if flag:
                cursor.execute("INSERT INTO rooms (id, name, password, id_admin) VALUES (?, ?, ?, ?)"
                                    ,(len(created_rooms), data["name"], data["password"], message.chat.id)
                )
                save_data = f"{len(created_rooms)}"
            conn.commit()
            await state.clear()
            await message.answer(f"Вы находитесь в главном меню вашей команты.", reply_markup=kb.menu_to_rooms_for_admin)
            await state.set_state(InRoomToAdmin.main_menu)
            await state.update_data(main_menu=save_data)
    else:
        await message.answer("Вы ввели некорректный пароль! Пароль должен состоять минимум из 8 символов и содержать только латинские буквы или цифры")
    
