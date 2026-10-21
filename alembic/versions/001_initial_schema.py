"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Resumes Table
    op.create_table(
        'resumes',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('filepath', sa.String(length=512), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False, server_default='pdf'),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('parsed_skills', sa.Text(), nullable=True),
        sa.Column('structured_profile', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_resumes_id'), 'resumes', ['id'], unique=False)
    op.create_index(op.f('ix_resumes_is_active'), 'resumes', ['is_active'], unique=False)

    # 2. Jobs Table
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('employment_type', sa.String(length=100), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='direct_url'),
        sa.Column('source_url', sa.String(length=1024), nullable=True),
        sa.Column('raw_description', sa.Text(), nullable=False),
        sa.Column('structured_jd', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_title'), 'jobs', ['title'], unique=False)
    op.create_index(op.f('ix_jobs_company'), 'jobs', ['company'], unique=False)
    op.create_index(op.f('ix_jobs_source_url'), 'jobs', ['source_url'], unique=False)

    # 3. Applications Table
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('jobs.id'), nullable=True),
        sa.Column('job_url', sa.String(length=1024), nullable=False),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('resume_id', sa.Integer(), sa.ForeignKey('resumes.id'), nullable=True),
        sa.Column('tailored_resume_id', sa.Integer(), sa.ForeignKey('resumes.id'), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('ats_score', sa.Float(), nullable=True),
        sa.Column('ats_feedback', sa.JSON(), nullable=True),
        sa.Column('tailored_resume_text', sa.Text(), nullable=True),
        sa.Column('tailored_resume_diff', sa.JSON(), nullable=True),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('submission_type', sa.String(length=50), nullable=False, server_default='manual'),
        sa.Column('submission_response', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_applications_id'), 'applications', ['id'], unique=False)
    op.create_index(op.f('ix_applications_status'), 'applications', ['status'], unique=False)

    # 4. Application Events Table
    op.create_table(
        'application_events',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('application_id', sa.Integer(), sa.ForeignKey('applications.id'), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.String(length=512), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index(op.f('ix_application_events_id'), 'application_events', ['id'], unique=False)
    op.create_index(op.f('ix_application_events_application_id'), 'application_events', ['application_id'], unique=False)

def downgrade() -> None:
    op.drop_table('application_events')
    op.drop_table('applications')
    op.drop_table('jobs')
    op.drop_table('resumes')
