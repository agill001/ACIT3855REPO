from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()

# # Update this with your MySQL database URI
# DATABASE_URI = 'mysql+pymysql://agill:123#Password@localhost:3306/lab4'
# engine = create_engine(DATABASE_URI)

DATABASE_URI = 'mysql+pymysql://user:Password@acit3855lab6.eastus.cloudapp.azure.com:3306/events'
engine = create_engine(DATABASE_URI)


class CreatePostEvent(Base):
    __tablename__ = 'create_post_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    postId = Column(String(50), nullable=False)
    content = Column(String(250))
    eventDetails = Column(JSON)
    userTags = Column(JSON)
    timestamp = Column(Integer)
    likesCount = Column(Integer)
    trace_id = Column(String(50))
    date_created = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "postId": self.postId,
            "content": self.content,
            "eventDetails": json.loads(self.eventDetails) if self.eventDetails else {},
            "userTags": json.loads(self.userTags) if self.userTags else [],
            "timestamp": self.timestamp,
            "likesCount": self.likesCount,
            "trace_id": self.trace_id,
            "date_created": self.date_created.strftime("%Y-%m-%dT%H:%M:%S")
        }


class FollowEvent(Base):
    __tablename__ = 'follow_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    eventId = Column(String(50), nullable=False)
    eventName = Column(String(100))
    followedBy = Column(String(50))
    followCount = Column(Integer)
    trace_id = Column(String(50))
    date_created = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "eventId": self.eventId,
            "eventName": self.eventName,
            "followedBy": self.followedBy,
            "followCount": self.followCount,
            "trace_id": self.trace_id,
            "date_created": self.date_created.strftime("%Y-%m-%dT%H:%M:%S")
        }


# Create tables
Base.metadata.create_all(engine)
