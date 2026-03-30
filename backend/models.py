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
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=True)
    organs_selected = Column(JSON, default=[])
    donation_mode = Column(String, default="general", nullable=False)  # general, after_death, relative
    relative_recipient_email = Column(String, nullable=True)  # Email of relative recipient for private donation
    is_deceased = Column(Boolean, default=False)
    deceased_at = Column(DateTime, nullable=True)
    medical_history = Column(Text, nullable=True)
    emergency_contact = Column(String, nullable=True)
    consent_agreed = Column(Boolean, default=False)
    status = Column(SAEnum(DonorStatus), default=DonorStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="donor_profile")
    hospital = relationship("Hospital")


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


class Hospital(Base):
    """Hospital registration and profiles"""
    __tablename__ = "hospitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    hospital_name = Column("name", String, nullable=True)
    registration_number = Column(String, unique=True, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    phone = Column("contact_phone", String, nullable=True)
    email = Column("contact_email", String, nullable=True)
    website = Column(String, nullable=True)
    bed_capacity = Column(Integer, nullable=True)
    specializations = Column(JSON, default=None, nullable=True)  # List of organ specialties
    is_verified = Column("is_active", Boolean, default=False, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")


class Recipient(Base):
    """Recipient profiles (similar to donor but for recipients)"""
    __tablename__ = "recipients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    blood_group = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    medical_condition = Column(String, nullable=True)
    organ_needed = Column(JSON, default=None, nullable=True)  # List of organs needed
    urgency = Column(String, default="standard", nullable=True)  # urgent, high, standard
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=True)
    hospital_contact_name = Column(String, nullable=True)
    
    # Verification tracking
    is_verified = Column(Boolean, default=False)
    status = Column(String, default="pending")  # pending, verified, approved, matched, completed, rejected
    
    # Documents and metadata
    documents = Column(JSON, default=None, nullable=True)  # List of document metadata
    verification_notes = Column(Text, nullable=True)  # Notes from recipient during submission
    reviewer_notes = Column(Text, nullable=True)  # Notes from admin reviewer
    
    # Timeline tracking
    submitted_at = Column(DateTime, nullable=True)  # When verification was submitted
    verified_at = Column(DateTime, nullable=True)  # When admin verified
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Admin user_id
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])
    hospital = relationship("Hospital")
    verifier = relationship("User", foreign_keys=[verified_by])


class Campaign(Base):
    """Awareness campaigns"""
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    content = Column(Text, nullable=True)
    icon = Column(String, default="🎯")  # Emoji or icon identifier
    campaign_type = Column(String, default="challenge")  # challenge, drive, event, other
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    target_participants = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User")
    participants = relationship("CampaignParticipant", back_populates="campaign", cascade="all, delete-orphan")


class CampaignParticipant(Base):
    """Tracks users participating in campaigns"""
    __tablename__ = "campaign_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    engagement_score = Column(Float, default=0.0)  # For tracking engagement

    campaign = relationship("Campaign", back_populates="participants")
    user = relationship("User")
    __table_args__ = ((__import__('sqlalchemy').UniqueConstraint('campaign_id', 'user_id', name='_campaign_user_uc'),))


class CommunityPost(Base):
    """Community/forum posts"""
    __tablename__ = "community_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    post_type = Column(String, default="story")  # story, discussion, question, etc.
    like_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")


class PostLike(Base):
    """Likes on community posts"""
    __tablename__ = "post_likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("CommunityPost", back_populates="likes")
    user = relationship("User")
    __table_args__ = ((__import__('sqlalchemy').UniqueConstraint('post_id', 'user_id', name='_post_user_like_uc'),))


class OrganRequest(Base):
    """Track organ requests/matches"""
    __tablename__ = "organ_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("donors.id"), nullable=True)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("recipients.id"), nullable=False)
    organ_type = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, matched, accepted, completed, rejected
    match_compatibility = Column(Float, nullable=True)  # 0.0 to 1.0
    request_date = Column(DateTime, default=datetime.utcnow)
    matched_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    donor = relationship("Donor")
    recipient = relationship("Recipient")


class MatchRequest(Base):
    """Track match requests between donor and recipient (for relative donation mode)"""
    __tablename__ = "match_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("donors.id"), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("recipients.id"), nullable=False)
    status = Column(String, default="pending")  # pending, accepted, rejected
    message = Column(Text, nullable=True)  # Optional message from donor
    requested_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    donor = relationship("Donor")
    recipient = relationship("Recipient")
