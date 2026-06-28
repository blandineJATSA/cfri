import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Float, Integer,
    DateTime, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


def now():
    return datetime.utcnow()


class UserRole(str, enum.Enum):
    admin = "admin"
    member = "member"
    viewer = "viewer"


class ImportType(str, enum.Enum):
    feedbacks = "feedbacks"
    orders = "orders"
    customers = "customers"


class ImportStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class SentimentEnum(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class UrgencyEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(String(50), default="free")
    clerk_org_id = Column(String(255), unique=True, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)
    users = relationship("User", back_populates="organization")
    imports = relationship("Import", back_populates="organization")
    customers = relationship("Customer", back_populates="organization")
    orders = relationship("Order", back_populates="organization")
    feedbacks = relationship("Feedback", back_populates="organization")
    problem_clusters = relationship("ProblemCluster", back_populates="organization")


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    clerk_user_id = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.member)
    created_at = Column(DateTime, default=now)
    organization = relationship("Organization", back_populates="users")


class Import(Base):
    __tablename__ = "imports"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    type = Column(SAEnum(ImportType), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=True)
    status = Column(SAEnum(ImportStatus), default=ImportStatus.pending)
    rows_total = Column(Integer, default=0)
    rows_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)
    completed_at = Column(DateTime, nullable=True)
    organization = relationship("Organization", back_populates="imports")
    feedbacks = relationship("Feedback", back_populates="import_source")


class Customer(Base):
    __tablename__ = "customers"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    total_spent = Column(Float, default=0.0)
    orders_count = Column(Integer, default=0)
    currency = Column(String(10), default="EUR")
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)
    organization = relationship("Organization", back_populates="customers")
    orders = relationship("Order", back_populates="customer")
    feedbacks = relationship("Feedback", back_populates="customer")
    risk_scores = relationship("CustomerRiskScore", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=False), ForeignKey("customers.id"), nullable=True)
    external_order_id = Column(String(255), nullable=True)
    order_date = Column(DateTime, nullable=True)
    total_amount = Column(Float, nullable=False)
    refund_amount = Column(Float, default=0.0)
    currency = Column(String(10), default="EUR")
    status = Column(String(50), nullable=True)
    product_name = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=now)
    organization = relationship("Organization", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")


class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    customer_id = Column(UUID(as_uuid=False), ForeignKey("customers.id"), nullable=True)
    import_id = Column(UUID(as_uuid=False), ForeignKey("imports.id"), nullable=True)
    channel = Column(String(100), nullable=True)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)
    feedback_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=now)
    organization = relationship("Organization", back_populates="feedbacks")
    customer = relationship("Customer", back_populates="feedbacks")
    import_source = relationship("Import", back_populates="feedbacks")
    analysis = relationship("FeedbackAnalysis", back_populates="feedback", uselist=False)


class FeedbackAnalysis(Base):
    __tablename__ = "feedback_analyses"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    feedback_id = Column(UUID(as_uuid=False), ForeignKey("feedbacks.id"), unique=True, nullable=False)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    sentiment = Column(SAEnum(SentimentEnum), nullable=True)
    urgency = Column(SAEnum(UrgencyEnum), nullable=True)
    root_cause = Column(Text, nullable=True)
    customer_intent = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    model_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=now)
    feedback = relationship("Feedback", back_populates="analysis")


class ProblemCluster(Base):
    __tablename__ = "problem_clusters"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    feedback_count = Column(Integer, default=0)
    customers_count = Column(Integer, default=0)
    associated_revenue = Column(Float, default=0.0)
    refund_amount = Column(Float, default=0.0)
    negative_rate = Column(Float, default=0.0)
    impact_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=now)
    updated_at = Column(DateTime, default=now, onupdate=now)
    organization = relationship("Organization", back_populates="problem_clusters")


class CustomerRiskScore(Base):
    __tablename__ = "customer_risk_scores"
    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    customer_id = Column(UUID(as_uuid=False), ForeignKey("customers.id"), nullable=False)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(SAEnum(RiskLevel), default=RiskLevel.low)
    reasons = Column(JSON, nullable=True)
    recommended_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)
    customer = relationship("Customer", back_populates="risk_scores")