from sqlalchemy import Column, Integer, String, Date, CHAR, Text, ForeignKey
from database.database import Base
class MissingPost(Base):
    __tablename__ = "missing_post"

    mp_id = Column(CHAR(36), primary_key=True, index=True)
    face_img_origin = Column(String(255))
    missing_date = Column(Date)
    missing_name = Column(String(45), nullable=False)
    missing_situation = Column(Text)
    missing_birth = Column(Date)
    missing_place = Column(String(100))
    missing_extra_evidence = Column(String(255))

    # FK
    user_id = Column(String(45), ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    gender_id = Column(Integer, ForeignKey("gender.gender_id"), nullable=False)

    class Config:
        orm_mode = True
class FamilyPost(Base):
    __tablename__ = "family_post"

    fp_id = Column(CHAR(36), primary_key=True, index=True)
    face_img_aging = Column(String(255))
    face_img_origin = Column(String(255))
    photo_age = Column(Integer)
    missing_birth = Column(Date, nullable=False)
    missing_date = Column(Date)
    missing_name = Column(String(45), nullable=False)
    missing_situation = Column(Text)
    missing_extra_evidence = Column(Text)
    missing_place = Column(String(100))

    # FK
    user_id = Column(String(45), ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    gender_id = Column(Integer, ForeignKey("gender.gender_id"), nullable=False)

    class Config:
        orm_mode = True
class Gender(Base):
    __tablename__ = "gender"

    gender_id = Column(Integer, primary_key=True, index=True)
    gender_name = Column(String(10), nullable=False)