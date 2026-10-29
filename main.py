from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


def get_expense_or_404(db: Session, expense_id: int) -> models.Expense:
    expense = db.get(models.Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    query = select(models.Expense).order_by(models.Expense.spent_on.desc())
    expenses = db.scalars(query).all()
    return templates.TemplateResponse(request, "index.html", {"expenses": expenses})


@app.get("/api/expenses", response_model=list[schemas.ExpenseRead])
def list_expenses(db: Session = Depends(get_db)):
    return db.scalars(select(models.Expense).order_by(models.Expense.id)).all()


@app.post("/api/expenses", response_model=schemas.ExpenseRead, status_code=201)
def create_expense(payload: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    expense = models.Expense(**payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@app.get("/api/expenses/{expense_id}", response_model=schemas.ExpenseRead)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    return get_expense_or_404(db, expense_id)


@app.put("/api/expenses/{expense_id}", response_model=schemas.ExpenseRead)
def update_expense(
    expense_id: int, payload: schemas.ExpenseCreate, db: Session = Depends(get_db)
):
    expense = get_expense_or_404(db, expense_id)
    for field, value in payload.model_dump().items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


@app.delete("/api/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = get_expense_or_404(db, expense_id)
    db.delete(expense)
    db.commit()