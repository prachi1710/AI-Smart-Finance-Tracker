from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal
import models, schemas
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import func, extract
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import calendar
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from passlib.context import CryptContext
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext

# ✅ Create a context for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create tables
Base.metadata.create_all(bind=engine)

# ✅ Create FastAPI app FIRST
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Pydantic schema
class UserCreate(BaseModel):
    name: str
    email: str
    monthly_income: float
    monthly_budget: float
    password: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Route
from sqlalchemy.exc import IntegrityError

@app.post("/users")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(
        name=user.name,
        email=user.email,
        monthly_income=user.monthly_income,
        monthly_budget=user.monthly_budget,
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
    
class TransactionCreate(BaseModel):
    user_id: int
    amount: float
    category: str
    description: str
    date: Optional[datetime] = None

@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    new_user = models.User(
        name=user.name,
        email=user.email,
        monthly_income=user.monthly_income,
        monthly_budget=user.monthly_budget,
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "name": new_user.name, "email": new_user.email}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # For simplicity, return user id (later you can use JWT token)
    return {"user_id": user.id, "name": user.name, "email": user.email}

@app.post("/transaction")
def add_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == transaction.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_txn = models.Transaction(
        user_id=transaction.user_id,
        amount=transaction.amount,
        category=transaction.category,
        description=transaction.description,
        date=transaction.date
    )
    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)
    return new_txn

@app.get("/dashboard/{user_id}")
def get_dashboard(
    user_id: int,
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Default to current month if not provided
    now = datetime.utcnow()
    month = month or now.month
    year = year or now.year

    # Filter transactions by month and year
    transactions_query = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        extract("month", models.Transaction.date) == month,
        extract("year", models.Transaction.date) == year
    )

    total_expense = transactions_query.with_entities(
        func.sum(models.Transaction.amount)
    ).scalar() or 0

    remaining_balance = user.monthly_income - total_expense
    is_over_budget = total_expense > user.monthly_budget
    if user.monthly_budget > 0:
        budget_usage_percent = (total_expense / user.monthly_budget) * 100
    else:
        budget_usage_percent = 0

    # Warning logic
    if budget_usage_percent < 70:
        warning_level = "Safe"
    elif budget_usage_percent < 90:
        warning_level = "Warning"
    else:
        warning_level = "Critical"

    category_data = transactions_query.with_entities(
        models.Transaction.category,
        func.sum(models.Transaction.amount)
    ).group_by(models.Transaction.category).all()

    category_breakdown = [
        {"category": c[0], "total": float(c[1] or 0)}
        for c in category_data
    ]

    return {
        "user_id": user.id,
        "user_name": user.name,
        "user_email": user.email,
        "month": month,
        "year": year,
        "income": user.monthly_income,
        "total_expense": float(total_expense),
        "remaining_balance": float(remaining_balance),
        "budget_usage_percent": round(budget_usage_percent, 2),
        "warning_level": warning_level,
        "is_over_budget": is_over_budget,
        "category_breakdown": category_breakdown
    }

@app.get("/insights/{user_id}")
def get_insights(
    user_id: int,
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.utcnow()
    month = month or now.month
    year = year or now.year

    transactions_query = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        extract("month", models.Transaction.date) == month,
        extract("year", models.Transaction.date) == year
    )

    total_expense = transactions_query.with_entities(
        func.sum(models.Transaction.amount)
    ).scalar() or 0

    if user.monthly_budget > 0:
        budget_usage_percent = (total_expense / user.monthly_budget) * 100
    else:
        budget_usage_percent = 0

    category_data = transactions_query.with_entities(
        models.Transaction.category,
        func.sum(models.Transaction.amount)
    ).group_by(models.Transaction.category).all()

    # Find highest spending category
    if category_data:
        top_category = max(category_data, key=lambda x: x[1])[0]
    else:
        top_category = None

    # Generate Insight
    if budget_usage_percent >= 90:
        insight = f"You have used {round(budget_usage_percent,2)}% of your monthly budget. Spending is critical. Most spending is in {top_category}. Consider reducing discretionary expenses immediately."
    elif budget_usage_percent >= 70:
        insight = f"You have used {round(budget_usage_percent,2)}% of your budget. Be cautious. {top_category} is your highest expense category."
    else:
        insight = f"Great job! You are within safe spending limits. Keep monitoring your {top_category} expenses."

    return {
        "month": month,
        "year": year,
        "budget_usage_percent": round(budget_usage_percent, 2),
        "top_spending_category": top_category,
        "insight": insight
    }

class MoodCreate(BaseModel):
    user_id: int
    mood: str

@app.post("/mood")
def create_mood(mood: MoodCreate, db: Session = Depends(get_db)):
    new_mood = models.Mood(
        user_id=mood.user_id,
        mood=mood.mood,
        date=datetime.utcnow()
    )
    db.add(new_mood)
    db.commit()
    db.refresh(new_mood)
    return new_mood

@app.get("/emotion-insights/{user_id}")
def emotion_insights(
    user_id: int,
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    month = month or now.month
    year = year or now.year

    # Get mood records for month
    moods = db.query(models.Mood).filter(
        models.Mood.user_id == user_id,
        extract("month", models.Mood.date) == month,
        extract("year", models.Mood.date) == year
    ).all()

    mood_spending = {}

    for mood_entry in moods:
        total = db.query(func.sum(models.Transaction.amount)).filter(
            models.Transaction.user_id == user_id,
            func.date(models.Transaction.date) == mood_entry.date
        ).scalar() or 0

        if mood_entry.mood in mood_spending:
            mood_spending[mood_entry.mood] += total
        else:
            mood_spending[mood_entry.mood] = total

    if mood_spending:
        highest_spending_mood = max(mood_spending, key=mood_spending.get)
        insight = f"You tend to spend the most when you feel {highest_spending_mood}."
    else:
        highest_spending_mood = None
        insight = "Not enough data to detect mood-based spending patterns."

    return {
        "month": month,
        "year": year,
        "mood_spending": mood_spending,
        "highest_spending_mood": highest_spending_mood,
        "insight": insight
    }

@app.get("/forecast/{user_id}")
def forecast_spending(
    user_id: int,
    month: int = None,
    year: int = None,
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    month = month or now.month
    year = year or now.year

    transactions = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        extract("month", models.Transaction.date) == month,
        extract("year", models.Transaction.date) == year
    ).all()

    if not transactions:
        return {"message": "Not enough data for prediction."}

    # Create dataframe
    data = []
    for t in transactions:
        day = t.date.day
        data.append({"day": day, "amount": t.amount})

    df = pd.DataFrame(data)

    # Aggregate daily spend
    daily_spend = df.groupby("day")["amount"].sum().reset_index()
    daily_spend = daily_spend.sort_values("day")

    # Cumulative spending
    daily_spend["cumulative"] = daily_spend["amount"].cumsum()

    X = daily_spend[["day"]].values
    y = daily_spend["cumulative"].values

    model = LinearRegression()
    model.fit(X, y)

    # Predict for day 30
    last_day = calendar.monthrange(year, month)[1]
    remaining_days = last_day - now.day
    if remaining_days <= 5:
    # Use last 7-day average
        last_7 = daily_spend.tail(7)
        avg_daily = last_7["amount"].mean()
        predicted_total = y[-1] + (avg_daily * remaining_days)
    else:
        predicted_total = model.predict(np.array([[last_day]]))[0]

    return {
        "month": month,
        "year": year,
        "predicted_month_end_spend": round(float(predicted_total), 2),
        "current_spend": round(float(y[-1]), 2)
    }