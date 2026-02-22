import sqlite3

from app.states import CreateRoom, EnterRoom, InRoomToAdmin
import app.keyboard as kb

from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.fsm.context import FSMContext


router_callback = Router()

"""        Callback для админа        """

@router_callback.callback_query(lambda c: c.data == "info_of_room")
async def btn_info_of_room(callback:CallbackQuery, state:FSMContext):
    await state.set_state(InRoomToAdmin.info_of_room)
    data = await state.get_data()
    data = data['main_menu']
    with sqlite3.connect("secret_santa.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms WHERE id=?", (int(data), ))
        get_bd = cursor.fetchone()
        await callback.message.answer(f"""Информация о комнате: 
                                            ID комнаты: {get_bd[0]}
                                            Название комнаты: {get_bd[1]}
                                            Пароль комнаты: {get_bd[2]}
                                            ID админа: {get_bd[3]}
                                    """)
    """
    await state.set_state(InRoomToAdmin.info_of_room)
    data = await state.get_data()
    data = data['main_menu'].split(";") + [f"{callback.message.chat.id}"]
    await callback.message.answer(f""Информация о комнате: 
                                        ID комнаты: {data[0]}
                                        Название комнаты: {data[1]}
                                        Пароль комнаты: {data[2]}
                                        ID админа: {data[3]}
                                "", reply_markup=kb.menu_for_info_of_room)
    """

@router_callback.callback_query(lambda c: c.data == "list_of_members")
async def btn_list_of_members(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data = data["main_menu"]
    keyboard, code = await kb.btns_list_members(int(data))
    if code == 0:
        await callback.message.edit_text("Список участников пуст", reply_markup=keyboard)
    else:
        await state.set_state(InRoomToAdmin.list_of_members)
        await callback.message.edit_text("Список участников: ", reply_markup=keyboard)

@router_callback.callback_query(F.data == "send_invite")
async def btn_send_invite(callback: CallbackQuery, state: FSMContext):
    await state.set_state(InRoomToAdmin.send_invite_name)
    await callback.message.answer("Введите имя пользователя, которому хотите отправить приглашение: ")

@router_callback.callback_query(F.data == "menu_room")
async def btn_menu_room(callback: CallbackQuery, state: FSMContext):
    await state.set_state(InRoomToAdmin.main_menu)
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
    await state.set_state(CreateRoom.name) # Установили статус создания комнаты для бота 
    await callback.message.answer("Придумайте название комнаты")

#Отловка кнопки Войти комнату
@router_callback.callback_query(F.data == "enter")
async def btn_enter(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EnterRoom.name_for_enter)
    await callback.message.answer("Введите название комнаты")

@router_callback.callback_query()
async def btn_room(callback: CallbackQuery, state: FSMContext):
    status_name = await state.get_state()
    print(status_name)
    match str(status_name):
        case "EnterRoom:name_for_enter":
            status = await state.get_data()
            data = status["name_for_enter"].split(";")
            if callback.data in data:
                s:str = callback.data
                await state.update_data(name_for_enter=s)
                await state.set_state(EnterRoom.password_for_enter)
                await callback.message.answer(f"Отлично! Теперь введите пароль от комнаты \"{s[s.index(' ')+1 : s.index('|')-1]}\"")
        case "InRoomToAdmin:list_of_members":
            await callback.message.edit_text("Выберите пункт меню:", reply_markup=kb.menu_for_member)
    
