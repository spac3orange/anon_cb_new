import json
from datetime import datetime
from app.database.db_session import Base
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Text, DECIMAL, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'users'

    record_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String, nullable=True)
    user_state = Column(String, default='Offline')


class Dialog(Base):
    __tablename__ = 'dialogs'

    record_id = Column(Integer, primary_key=True, autoincrement=True)
    dialog_date = Column(DateTime)
    dialog_id = Column(BigInteger)
    user_1_id = Column(BigInteger, nullable=False)
    user_2_id = Column(BigInteger, nullable=False)
    media_path = Column(String, nullable=True)
    dialog_status = Column(String, default='Open')






