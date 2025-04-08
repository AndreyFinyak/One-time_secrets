from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Базовая схема для секрета
class SecretBase(BaseModel):
    secret: str
    passphrase: Optional[str] = None 
    ttl_seconds: Optional[int] = None 

    class Config:
        from_attributes = True

# Схема для создания секрета
class SecretCreate(SecretBase):
    pass

# Схема для представления секрета в ответе
class Secret(SecretBase):
    id: int  

    class Config:
        orm_mode = True


class SecretResponse(BaseModel):
    id: int
    hashed_secret: str  
    created_at: datetime
    expire_at: Optional[datetime]  
    meta_data: Optional[str] = None  

    class Config:
        from_attributes = True
