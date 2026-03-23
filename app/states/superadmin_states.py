from aiogram.fsm.state import State, StatesGroup


class SuperAdminStates(StatesGroup):
    edit_prompt = State()        # waiting for new AI prompt text
    upload_parts_csv = State()   # waiting for CSV file
    enter_shop_name = State()    # waiting for shop name when creating invite
