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
async def cmd_start(message: Message, state: FSMContext):
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
        cursor.execute("SELECT name FROM users WHERE id=?", (message.chat.id, ))
        data = cursor.fetchone()
        if data == None:
            print("Такого пользователя не существует")
            await state.set_state(sts.InfoOfUser.name)
            await message.answer("Вы еще не зарегестрированы в боте, пожалуйста введите свой ник")
        else:
            await message.answer(f"Добро пожаловать, {data[0]}, в игру \"Тайный санта в тгэшке\". Выберете пункт меню:", reply_markup=kb.main)

@router_enter.message(sts.InfoOfUser.name)
async def enterName(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(sts.InfoOfUser.await_answer)
    await message.answer(f"Подтвердите свой никнейм. Вы ввели <b>{message.text}</b>. Если что, никнейм всегда можно изменить в настройках", 
                         parse_mode="html", reply_markup=kb.switch_name)

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
            await state.set_state(sts.EnterRoom.password_for_enter)
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
                await state.set_state(sts.InRoomToPlayer.main_menu)
                await state.update_data(main_menu=id)
                cursor.execute("SELECT users FROM rooms WHERE id = ?", (id, ))
                get_bd = cursor.fetchone()[0]
                get_bd = f'{get_bd}_' if get_bd != None else ''
                if get_bd == "" or not(str(message.chat.id) in get_bd.split('_')):
                    cursor.execute(f"UPDATE rooms SET users = ? WHERE id=?", (f"{get_bd+str(message.chat.id)}", id))
                    conn.commit()
                await message.answer(f"Вы находитесь в главном меню {name} команты.", reply_markup=kb.menu_to_rooms_for_player)



"""     Состояния создания комнат      """

#Отловка сообщения пользователя в статусе написания НАЗВАНИЯ комнаты
@router_enter.message(sts.CreateRoom.name)
async def stage_first(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(sts.CreateRoom.password)
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
            await state.set_state(sts.InRoomToAdmin.main_menu)
            await state.update_data(main_menu=save_data)
    else:
        await message.answer("Вы ввели некорректный пароль! Пароль должен состоять минимум из 8 символов и содержать только латинские буквы или цифры")
    