from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    job_url = Column(String(1024), nullable=False)
    job_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    tailored_resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    
    # Truthful lifecycle status: draft, ready_for_review, submission_in_progress, submitted,
    # interviewing, rejected, offer, requires_manual_action, failed
    status = Column(String(50), default="draft", index=True, nullable=False)
    
    ats_score = Column(Float, nullable=True)
    ats_feedback = Column(JSON, nullable=True)  # Detailed breakdown & actionable suggestions
    
    tailored_resume_text = Column(Text, nullable=True)
    tailored_resume_diff = Column(JSON, nullable=True)  # Summary of changes and before/after stats
    cover_letter = Column(Text, nullable=True)
    
    # Submission tracking
    submission_type = Column(String(50), default="manual", nullable=False)
    submission_response = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resume = relationship("Resume", foreign_keys=[resume_id])
    tailored_resume = relationship("Resume", foreign_keys=[tailored_resume_id])
    job = relationship("Job", foreign_keys=[job_id])
    events = relationship("ApplicationEvent", back_populates="application", cascade="all, delete-orphan", order_by="ApplicationEvent.created_at.desc()")

class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # created, analyzed, tailored, status_changed, submitted, email_sent, error
    message = Column(String(512), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="events")
