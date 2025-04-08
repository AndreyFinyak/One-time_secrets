from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Secret(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    secret_key = Column(String, unique=True, index=True, nullable=False)
    secret = Column(String, nullable=False)
    passphrase = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

class SecretLog(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    secret_id = Column(Integer, ForeignKey("secrets.id"), nullable=True)
    ip_address = Column(String)
    meta_data = Column(JSON, nullable=True)  
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
