from pydantic import BaseModel, constr
from datetime import datetime
from typing import Optional

# Schema for creating a transaction
class TransactionCreate(BaseModel):
    user_id: int
    amount: float
    category: str
    description: Optional[str] = ""
    date: datetime

# Schema for creating a user (optional)
class UserCreate(BaseModel):
    name: str
    email: str           # add email
    monthly_income: float
    monthly_budget: float
    password: constr(min_length=6, max_length=72)
    