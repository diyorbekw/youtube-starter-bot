from aiogram.fsm.state import StatesGroup, State

class UploadStates(StatesGroup):
    waiting_topic = State()
    waiting_video_file = State()

class LogoGenerationStates(StatesGroup):
    waiting_description = State()
    waiting_style = State()
    waiting_confirmation = State()
    
class BannerGenerationStates(StatesGroup):
    waiting_description = State()
    waiting_style = State()
    waiting_confirmation = State()