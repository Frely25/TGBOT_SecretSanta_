from aiogram.fsm.state import State, StatesGroup

class CreateRoom(StatesGroup):
    name = State()
    password = State()

class EnterRoom(StatesGroup):
    name_for_enter = State()
    password_for_enter = State()
    choose_room = State()

class InRoomToAdmin(StatesGroup):
    name_room = State()
    old_password = State()
    new_password = State()
    main_menu = State()
    info_of_room = State()
    list_of_members = State()
    send_invite_name = State()

class InRoomToPlayer(StatesGroup):
    main_menu = State()
    info_of_room = State()
    list_of_members = State()

    