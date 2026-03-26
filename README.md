# 💰 AI Smart Finance Tracker

An intelligent, full-stack finance tracking application that helps users manage expenses, monitor spending behavior, and gain actionable financial insights using AI.

---

## 🚀 Features

### 📊 Financial Dashboard
- View income, expenses, and remaining balance
- Budget tracking with real-time status (Within Budget / Over Budget)
- Visual insights with charts

### 📈 AI-Based Spending Forecast
- Predicts month-end spending using machine learning
- Helps users proactively manage finances

### 🧠 Smart Alerts
- Alerts when:
  - Budget exceeds limits
  - Spending crosses 80% of income
  - Remaining balance is low
- Category-level anomaly detection

### 📂 Category-wise Insights
- Pie chart visualization of spending
- Identifies top spending categories

### 📅 Monthly Spending Trend
- Tracks spending patterns over time
- Helps in understanding financial habits

### 😊 Mood-Based Spending Analysis
- Log daily mood
- Detect correlation between emotions and spending behavior

### 🔐 Authentication System
- User Registration & Login
- Personalized dashboard for each user

---

## 🏗️ Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- Scikit-learn (ML model for forecasting)
- Pandas & NumPy

### Frontend
- React.js
- CSS
- Recharts (for data visualization)

---

## 📌 Architecture

- RESTful APIs built using FastAPI
- Separate frontend (React) and backend
- Database-driven system with user-specific data
- ML model integrated for predictions

---

## ⚙️ Setup Instructions

### 🔹 Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

🔹 Frontend Setup
cd smart-finance-frontend
npm install
npm start
