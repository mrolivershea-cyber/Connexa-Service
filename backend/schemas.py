from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str

class UserCreate(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Node schemas  
class NodeBase(BaseModel):
    ip: str
    port: Optional[int] = None
    login: Optional[str] = ""
    password: Optional[str] = ""
    provider: Optional[str] = ""
    country: Optional[str] = ""
    state: Optional[str] = ""
    city: Optional[str] = ""
    zipcode: Optional[str] = ""
    comment: Optional[str] = ""
    protocol: Optional[str] = "pptp"
    status: Optional[str] = "not_tested"
    speed: Optional[str] = None
    
    # SOCKS Proxy data
    socks_ip: Optional[str] = None
    socks_port: Optional[int] = None
    socks_login: Optional[str] = None
    socks_password: Optional[str] = None
    
    # OVPN Configuration  
    ovpn_config: Optional[str] = None
    
    # Scamalytics data
    scamalytics_fraud_score: Optional[int] = None
    scamalytics_risk: Optional[str] = None

class NodeCreate(NodeBase):
    pass

class NodeUpdate(BaseModel):
    ip: Optional[str] = None
    port: Optional[int] = None
    login: Optional[str] = None
    password: Optional[str] = None
    provider: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    zipcode: Optional[str] = None
    comment: Optional[str] = None
    protocol: Optional[str] = None
    status: Optional[str] = None
    speed: Optional[str] = None
    
    # SOCKS Proxy data
    socks_ip: Optional[str] = None
    socks_port: Optional[int] = None
    socks_login: Optional[str] = None
    socks_password: Optional[str] = None
    
    # OVPN Configuration
    ovpn_config: Optional[str] = None

class Node(NodeBase):
    id: int
    last_check: Optional[datetime] = None
    last_update: datetime
    created_at: datetime
    
    # SOCKS Proxy data
    socks_ip: Optional[str] = None
    socks_port: Optional[int] = None
    socks_login: Optional[str] = None
    socks_password: Optional[str] = None
    
    # OVPN Configuration
    ovpn_config: Optional[str] = None
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

# Import/Export schemas
class BulkImport(BaseModel):
    data: str
    protocol: str = "pptp"

class ImportNodesSchema(BaseModel):
    data: str
    protocol: str = "pptp"
    testing_mode: str = "no_test"  # ping_only, speed_only, no_test

class ExportRequest(BaseModel):
    node_ids: List[int]
    format: str = "txt"  # txt, csv, xlsx

# Service Management schemas
class ServiceAction(BaseModel):
    node_ids: List[int]
    action: str  # start, stop, restart

class TestRequest(BaseModel):
    node_ids: Optional[List[int]] = []  # Empty list means "test all nodes" or use filters
    test_type: str = "ping"  # ping, speed
    filters: Optional[dict] = {}  # Filters for Select All mode (status, country, etc.)
    # Optional tuning
    ping_concurrency: Optional[int] = None
    speed_concurrency: Optional[int] = None
    ping_timeouts: Optional[List[float]] = None  # seconds per attempt, e.g., [0.8,1.2,1.6]
    speed_sample_kb: Optional[int] = None        # e.g., 512
    speed_timeout: Optional[int] = None          # total timeout seconds

class ServiceStatus(BaseModel):
    node_id: int
    active: bool
    services: List[str]
    interface: Optional[str] = None
    socks_port: Optional[int] = None
    socks_ip: Optional[str] = None
    uptime: Optional[float] = None

class TestResult(BaseModel):
    node_id: int
    ip: str
    test_type: str
    ping: Optional[dict] = None
    speed: Optional[dict] = None
    overall: str  # online, offline, degraded
    tested_at: datetime
