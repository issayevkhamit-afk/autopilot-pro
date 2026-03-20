from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    # Labor prices
    waiting_labor_name = State()
    waiting_labor_price = State()
    waiting_labor_category = State()

    # Parts
    waiting_parts_file = State()
    waiting_part_name = State()
    waiting_part_price = State()

    # Shop settings
    waiting_shop_name = State()
    waiting_shop_city = State()
    waiting_shop_phone = State()
    waiting_logo = State()
