from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    employment_type = Column(String(100), nullable=True)
    source = Column(String(100), default="direct_url", nullable=False)
    source_url = Column(String(1024), nullable=True, index=True)
    raw_description = Column(Text, nullable=False)
    structured_jd = Column(JSON, nullable=True)  # Normalized title, skills, yoe, reqs
    status = Column(String(50), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
