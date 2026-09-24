from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    room_number = State()
    sbp_phone = State()
    sbp_bank = State()


class CreateRideStates(StatesGroup):
    from_location = State()
    custom_from = State()
    to_location = State()
    custom_to = State()
    meeting_point = State()
    custom_meeting = State()
    departure_time = State()
    custom_time = State()
    max_seats = State()
    confirm = State()


class SplitPaymentStates(StatesGroup):
    total_cost = State()