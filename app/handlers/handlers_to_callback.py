import sqlite3

import app.states as sts
import app.keyboard as kb

from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.fsm.context import FSMContext


router_callback = Router()

"""        Callback для админа        """

@router_callback.callback_query(lambda c: c.data == "info_of_room")
async def btn_info_of_room(callback:CallbackQuery, state:FSMContext):
    print(callback.message.message_id)
    await state.set_state(sts.InRoomToAdmin.info_of_room)
    await state.update_data(info_of_room=f"{callback.message.message_id}")
    data = await state.get_data()
    data = data['main_menu']
    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms WHERE id=?", (int(data), ))
        get_bd = cursor.fetchone()
        await callback.message.delete()
        await callback.message.answer(f"""Информация о комнате: 
ID комнаты: {get_bd[0]}
Название комнаты: {get_bd[1]}
Пароль комнаты: {get_bd[2]}
ID админа: {get_bd[3]}""", reply_markup=kb.menu_for_info_of_room)
    

@router_callback.callback_query(lambda c: c.data == "list_of_members")
async def btn_list_of_members(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data = data["main_menu"]
    keyboard, code = await kb.btns_list_members(int(data))
    if code == 0:
        await callback.message.edit_text("Список участников пуст", reply_markup=keyboard)
    else:
        await state.set_state(sts.InRoomToAdmin.list_of_members)
        await callback.message.edit_text("Список участников: ", reply_markup=keyboard)

@router_callback.callback_query(F.data == "send_invite")
async def btn_send_invite(callback: CallbackQuery, state: FSMContext):
    await state.set_state(sts.InRoomToAdmin.send_invite_name)
    await callback.message.edit_text("Введите имя пользователя, которому хотите отправить приглашение: ")

@router_callback.callback_query(F.data == "menu_room")
async def btn_menu_room(callback: CallbackQuery, state: FSMContext):
    await state.set_state(sts.InRoomToAdmin.main_menu)
    await callback.message.edit_text(f"Вы находитесь в главном меню вашей команты.", reply_markup=kb.menu_to_rooms_for_admin)


@router_callback.callback_query(F.data == "main_menu")
async def btn_main_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(f"Добро пожаловать, {callback.message.from_user.first_name},в игру \"Тайный санта в тгэшке\".\nВыберете пункт меню:",
                         reply_markup=kb.main)

@router_callback.callback_query(F.data == "back")
async def btn_back(callback: CallbackQuery, state: FSMContext):
     data = await state.get_data()
     data = data["main_menu"]
     await callback.message.edit_text("Список участников: ", reply_markup= await kb.btns_list_members(int(data)))


"""        Callback для входа         """


#Отловка кнопки Создать комнату
@router_callback.callback_query(F.data == "create")
async def btn_create(callback: CallbackQuery, state: FSMContext):
    await state.set_state(sts.CreateRoom.name) # Установили статус создания комнаты для бота 
    await callback.message.answer("Придумайте название комнаты")

#Отловка кнопки Войти комнату
@router_callback.callback_query(F.data == "enter")
async def btn_enter(callback: CallbackQuery, state: FSMContext):
    await state.set_state(sts.EnterRoom.name_for_enter)
    await callback.message.answer("Введите название комнаты")

#Откловка кнопки Информация обо мне 
@router_callback.callback_query(F.data == "info_about_me")
async def btn_info_about_me(callback: CallbackQuery):
    await callback.message.answer(f"""Имя: {callback.message.chat.first_name}
Chat id: {callback.message.chat.id}""", reply_markup=kb.main)

@router_callback.callback_query(F.data == "accept")
async def btn_accept(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    print(data)
    data = data["main_menu"]
    await state.set_state(sts.InRoomToPlayer.main_menu)
    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM rooms WHERE id = ?", (int(data), ))
        data = cursor.fetchone()
        await callback.message.edit_text(f"Вы находитесь в главном меню {data[0]} команты.", reply_markup=kb.menu_to_rooms_for_player)


@router_callback.callback_query(lambda c: c.data.startswith("join_"))
async def btn_invite(callback: CallbackQuery, state: FSMContext):
    room_id = int(callback.data.split("_")[1])
    await state.set_state(sts.InRoomToPlayer.main_menu)
    await state.update_data(main_menu=f"{room_id}")
    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, users FROM rooms WHERE id = ?", (room_id, ))
        data = cursor.fetchone()
        get_bd = f'{data[1]}_' if data[1] != None else ''
        print(f"get_bd = {get_bd}")
        print(f"data[1] = {data[1]}")
        if get_bd == "" or not(str(callback.message.chat.id) in get_bd.split('_')):
            cursor.execute(f"UPDATE rooms SET users = ? WHERE id=?", (f"{get_bd+str(callback.message.chat.id)}", room_id))
            conn.commit()
        await callback.message.edit_text(f"Вы находитесь в главном меню {data[0]} команты.", reply_markup=kb.menu_to_rooms_for_player)

@router_callback.callback_query(F.data == "refuse")
async def btn_refuse(callback: CallbackQuery):
    await callback.message.edit_text(f"Добро пожаловать, {callback.message.from_user.first_name},в игру \"Тайный санта в тгэшке\".\nВыберете пункт меню:", reply_markup=kb.main)


"""         Callback для отловки массива callback`ов        """


@router_callback.callback_query()
async def btn_room(callback: CallbackQuery, state: FSMContext):
    status_name = await state.get_state()
    #print(status_name)
    match str(status_name):
        case "EnterRoom:name_for_enter":
            status = await state.get_data()
            data = status["name_for_enter"].split(";")
            if callback.data in data:
                s:str = callback.data
                await state.update_data(name_for_enter=s)
                await state.set_state(sts.EnterRoom.password_for_enter)
                await callback.message.answer(f"Отлично! Теперь введите пароль от комнаты \"{s[s.index(' ')+1 : s.index('|')-1]}\"")
        case "InRoomToAdmin:list_of_members":
            await callback.message.edit_text("Выберите пункт меню:", reply_markup=kb.menu_for_member)
        case "InRoomToAdmin:send_invite_name":
            data = await state.get_data()
            data = data["send_invite_name"].split("_")
            if callback.data in data:
                await callback.message.bot.send_message(chat_id=int(callback.data), text=f"Пользователь {callback.message.chat.first_name} отправил вам предложение вступить в комнату", reply_markup=kb.menu_to_invited)
    
