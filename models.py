import datetime

from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]
    amount: Mapped[float]
    category: Mapped[str]
    spent_on: Mapped[datetime.date]