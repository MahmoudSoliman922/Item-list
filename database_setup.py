from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    email = Column(String(80) , nullable=False)
    picture = Column(String(250))

class Competetion(Base):
    __tablename__ = 'competetion'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,

       }
 
class Team(Base):
    __tablename__ = 'team'

    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    competetion_id = Column(Integer,ForeignKey('competetion.id'))
    competetion = relationship(Competetion)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'         : self.id,
       }

class Player(Base):
    __tablename__ = 'player'

    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    position = Column(String(80))
    number = Column(String(80))
    dob = Column(String(80))
    nationality = Column(String(80))
    contract = Column(String(80))
    marketvalue = Column(String(80))
    team_id = Column(Integer,ForeignKey('team.id'))
    team = relationship(Team)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'position'         : self.position,
           'id'         : self.id,
           'number'         : self.number,
           'dob'             : self.dob,
           'nationality'     : self.nationality,
           'contract'             : self.contract,
           'marketvalue'             : self.marketvalue,
       }
    
engine = create_engine('sqlite:///footballinfo.db')
 

Base.metadata.create_all(engine)
