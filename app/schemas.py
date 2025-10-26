from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    firebase_token: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    firebase_token: Optional[str] = None
    class Config:
        from_attributes = True

class RouteCreate(BaseModel):
    user_id: int
    departure_name: str = Field(..., examples=["Torino Porta Susa"])
    arrival_name: str = Field(..., examples=["Milano Centrale"])
    train_number: Optional[str] = None
    active: bool = True

class RouteOut(BaseModel):
    id: int
    user_id: int
    departure_name: str
    arrival_name: str
    departure_code: str
    arrival_code: str
    train_number: Optional[str]
    active: bool
    class Config:
        from_attributes = True

class TrainStatusOut(BaseModel):
    id: int
    route_id: int
    train_code: str
    last_status: str
    delay_minutes: int
    last_update: datetime
    class Config:
        from_attributes = True

class NotifyTestIn(BaseModel):
    user_id: int
    title: str
    body: str
