import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from database import Base


class UserRole(str, enum.Enum):
    donor = "donor"
    recipient = "recipient"
    hospital = "hospital"
    admin = "admin"


class DonorStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ContentType(str, enum.Enum):
    myth = "myth"
    faq = "faq"
    blog = "blog"
    legal = "legal"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.donor, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    donor_profile = relationship("Donor", back_populates="user", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="user")


class Donor(Base):
    __tablename__ = "donors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    full_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    blood_group = Column(String, nullable=False)
    location = Column(String, nullable=False)
    organs_selected = Column(JSON, default=[])
    medical_history = Column(Text, nullable=True)
    emergency_contact = Column(String, nullable=True)
    consent_agreed = Column(Boolean, default=False)
    status = Column(SAEnum(DonorStatus), default=DonorStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="donor_profile")


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region = Column(String, nullable=False)
    organ_type = Column(String, nullable=False)
    predicted_demand = Column(Float, nullable=False)
    instability_index = Column(Float, nullable=True)
    available_supply = Column(Float, default=0.0)
    registered_donors = Column(Integer, default=0)
    confidence_score = Column(Float, nullable=True)
    model_version = Column(String, default="1.0")
    created_at = Column(DateTime, default=datetime.utcnow)


class AwarenessContent(Base):
    __tablename__ = "awareness_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    type = Column(SAEnum(ContentType), nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    query = Column(Text, nullable=False)
    classification = Column(String, nullable=False)   # organ_related / non_organ_related
    response = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_date = Column(DateTime, default=datetime.utcnow)
    accuracy = Column(Float, nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    dataset_hash = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    metrics = Column(JSON, nullable=True)
    version_tag = Column(String, nullable=True)


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String, nullable=False)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    r2_score = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    feature_importance = Column(JSON, nullable=True)
    training_samples = Column(Integer, nullable=True)
    trained_at = Column(DateTime, default=datetime.utcnow)


class SessionToken(Base):
    """Server-side session management"""
    __tablename__ = "session_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    refresh_token_hash = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecipientVerification(Base):
    """Server-side recipient verification form data"""
    __tablename__ = "recipient_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String, default="not_started")  # not_started, in_progress, submitted, approved, rejected
    current_step = Column(Integer, default=1)
    
    # Personal details
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    dob = Column(String, nullable=True)
    
    # Medical history
    medical_condition = Column(String, nullable=True)
    transplant_type = Column(String, nullable=True)
    medical_notes = Column(Text, nullable=True)
    
    # Hospital reference
    hospital_name = Column(String, nullable=True)
    hospital_contact = Column(String, nullable=True)
    hospital_city = Column(String, nullable=True)
    
    # Consent
    consent_agreed = Column(Boolean, default=False)
    consent_date = Column(String, nullable=True)
    
    # File uploads (store URLs/metadata only)
    documents = Column(JSON, default={})  # { "medicalReports": [...], "idProof": {...}, ... }
    
    # Metadata
    submitted_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FileUpload(Base):
    """Track uploaded files with metadata"""
    __tablename__ = "file_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    verification_id = Column(UUID(as_uuid=True), ForeignKey("recipient_verifications.id"), nullable=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # e.g., "medicalReports", "idProof"
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_url = Column(String, nullable=False)  # S3/storage URL
    file_hash = Column(String, nullable=True)  # For integrity check
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    """Track all user actions for security auditing"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # nullable for system actions
    action = Column(String, nullable=False, index=True)  # e.g., "USER_LOGIN", "VERIFICATION_SUBMITTED"
    details = Column(JSON, default={})  # Contextual data like IP, user agent, etc.
    ip_address = Column(String, nullable=True)
    # user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")
