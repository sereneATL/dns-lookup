import time
from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ARRAY
from sqlalchemy.orm import relationship

class QueryLog(Base):
    __tablename__ = "query_logs"
    id = Column(Integer,primary_key=True,nullable=False)
    domain = Column(String, nullable=False)
    client_ip = Column(String, nullable=False)
    addresses = Column(ARRAY(String), nullable=False)
    created_at = Column(Integer, default=int(time.time()))