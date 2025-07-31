from aiogram.fsm.state import State, StatesGroup

class AddOrder(StatesGroup):
    name = State()
    platform = State()
    link = State()
    payment_status = State()
    comment = State()
    confirmation = State()
    editing_field = State()

class EditOrder(StatesGroup):
    select_field = State()
    get_new_value = State()

class AddPlatform(StatesGroup):
    name = State()

class DeletePlatform(StatesGroup):
    select = State()