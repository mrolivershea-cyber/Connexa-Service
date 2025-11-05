from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy import event
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
import hashlib

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./connexa.db")

# Optimized SQLite engine for better concurrent performance
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    poolclass=NullPool,  # Disable pooling to avoid QueuePool timeouts with SQLite
    connect_args={
        "check_same_thread": False,
        "timeout": 120,
        "isolation_level": "DEFERRED"
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
        # Automatically commit after successful operation
        db.commit()
    except Exception as e:
        # Rollback on any error
        db.rollback()
        raise
    finally:
        db.close()

# User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Node model
class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String(45), index=True, nullable=False)
    port = Column(Integer, nullable=True)  # Port for the service
    login = Column(String(100), index=True, default="")
    password = Column(String(255), default="")
    provider = Column(String(100), index=True, default="")
    country = Column(String(100), index=True, default="")
    state = Column(String(100), index=True, default="")
    city = Column(String(100), index=True, default="")
    zipcode = Column(String(20), index=True, default="")
    comment = Column(Text, default="")
    protocol = Column(String(10), index=True, default="pptp")  # pptp, ssh, socks, server
    status = Column(String(20), index=True, default="not_tested")  # Unified status: not_tested, ping_failed, ping_ok, speed_ok, offline, online
    speed = Column(String(20), nullable=True)  # Connection speed in Mbps
    
    # SOCKS Proxy data (populated when services are launched)
    socks_ip = Column(String(45), nullable=True)  # SOCKS proxy IP
    socks_port = Column(Integer, nullable=True)   # SOCKS proxy port  
    socks_login = Column(String(100), nullable=True)  # SOCKS proxy login
    socks_password = Column(String(255), nullable=True)  # SOCKS proxy password
    previous_status = Column(String(20), nullable=True)  # Status before SOCKS launch (for proper restoration)
    ppp_interface = Column(String(20), nullable=True)  # PPP interface name (ppp0, ppp1, etc.)
    
    # OVPN Configuration (populated when services are launched)
    ovpn_config = Column(Text, nullable=True)  # Complete OVPN configuration
    
    # Scamalytics data (fraud detection)
    scamalytics_fraud_score = Column(Integer, nullable=True, default=None)  # Fraud score 0-100
    scamalytics_risk = Column(String(20), nullable=True, default=None)  # Risk level: low, medium, high
    
    last_check = Column(DateTime, nullable=True)
    last_update = Column(DateTime, nullable=True)  # Explicitly set in Python code, not by DB
    created_at = Column(DateTime, server_default=func.now())

def create_tables():
    Base.metadata.create_all(bind=engine)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
