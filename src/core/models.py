from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    h1_handle = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    scopes = relationship("Scope", back_populates="program")

class Scope(Base):
    __tablename__ = "scopes"
    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey("programs.id"))
    identifier = Column(String) # e.g. *.example.com
    scope_type = Column(String) # e.g. wildcard, domain, ip
    is_active = Column(Boolean, default=True)
    program = relationship("Program", back_populates="scopes")

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    value = Column(String, unique=True) # e.g. dev.example.com
    asset_type = Column(String) # subdomain, ip, url
    priority_score = Column(Integer, default=0)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    metadata_json = Column(JSON) # Store tech, status codes, etc.

class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    title = Column(String)
    severity = Column(String)
    description = Column(String)
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
