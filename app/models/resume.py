from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime
from app.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    file_type = Column(String(20), default="pdf", nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    raw_text = Column(Text, nullable=False)
    parsed_skills = Column(Text, nullable=True)  # Comma-separated normalized skills
    structured_profile = Column(JSON, nullable=True)  # Detailed extracted sections
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
