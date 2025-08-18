from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tg_id = Column(String(64), unique=True, index=True, nullable=False)
    google_connected = Column(Boolean, default=False, nullable=False)
    last_oauth_update = Column(DateTime)
    google_refresh_token = Column(Text)
    google_token_json = Column(Text)
    yt_channel_id = Column(String(128))
    created_at = Column(DateTime, default=datetime.now(), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now()) 


    videos = relationship("VideoJob", back_populates="user")
    logo_jobs = relationship("LogoJob", back_populates="user")
    banner_jobs = relationship("BannerJob", back_populates="user")

class VideoJob(Base):
    __tablename__ = "video_jobs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    topic = Column(String(255))
    title = Column(String(255))
    description = Column(Text)
    tags = Column(Text)  
    file_path = Column(Text)
    thumbnail_path = Column(Text)
    yt_video_id = Column(String(64))
    status = Column(String(32), default="draft") 

    created_at = Column(DateTime, default=datetime.now())
    user = relationship("User", back_populates="videos")

class LogoJob(Base):
    __tablename__ = "logo_jobs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(String)
    style = Column(String)
    prompt = Column(String)
    image_url = Column(String)
    filename = Column(String)
    status = Column(String) 
    created_at = Column(DateTime)
    
    user = relationship("User", back_populates="logo_jobs")
    
class BannerJob(Base):
    __tablename__ = "banner_jobs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(String)
    style = Column(String)
    prompt = Column(String)
    image_url = Column(String)
    filename = Column(String)
    status = Column(String) 
    created_at = Column(DateTime)
    
    user = relationship("User", back_populates="banner_jobs")