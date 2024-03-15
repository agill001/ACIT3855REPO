from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class SportGramStats(Base):
    __tablename__ = 'sportgram_stats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    num_create_posts = Column(Integer, default=0, nullable=False)
    num_follow_events = Column(Integer, default=0, nullable=False)
    total_likes = Column(Integer, default=0, nullable=False)
    total_follow_count = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "num_create_posts": self.num_create_posts,
            "num_follow_events": self.num_follow_events,
            "total_likes": self.total_likes,
            "total_follow_count": self.total_follow_count,
            "last_updated": self.last_updated.strftime("%Y-%m-%d %H:%M:%S")
        }


engine = create_engine('sqlite:///stats.sqlite')
Base.metadata.create_all(engine)
