from sqlalchemy import Column, Integer, String

from db.session import Base

# FAQ MODEL


class Faq(Base):
    __tablename__ = "faq"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    solution = Column(String)
    tag = Column(String)
