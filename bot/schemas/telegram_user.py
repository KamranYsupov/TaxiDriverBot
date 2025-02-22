from typing import Optional

from pydantic import BaseModel


class TelegramUserBaseSchema(BaseModel):
    telegram_id: int 
    username: Optional[str]
    
    
class TelegramUserSchema(TelegramUserBaseSchema):
    id: int 
    

class TelegramUserCreateSchema(TelegramUserBaseSchema):
    pass