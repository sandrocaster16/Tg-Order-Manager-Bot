from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())

class Platform(Base):
    __tablename__ = 'platforms'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # ИЗМЕНЕНО: убрана опасная каскадная политика 'all, delete-orphan'
    orders = relationship("Order", back_populates="platform")

class Order(Base):
    __tablename__ = 'orders'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform_id: Mapped[int] = mapped_column(ForeignKey('platforms.id'), nullable=False)
    
    link: Mapped[str] = mapped_column(String(255), nullable=True) # Ссылку можно не указывать
    
    payment_status: Mapped[str] = mapped_column(String(50), default="Ожидает")
    comment: Mapped[str] = mapped_column(String(500), nullable=True)
    
    platform = relationship("Platform", back_populates="orders", lazy="joined")