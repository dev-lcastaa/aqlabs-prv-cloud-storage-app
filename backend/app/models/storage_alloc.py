from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class StorageAlloc(Base):
    __tablename__ = "storage_alloc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_index: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)
