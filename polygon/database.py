import json
from env import env
from pathlib import Path
from sqlalchemy import create_engine, Column, String, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine(env.DATABASE_URL)
Base = declarative_base(bind=engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, autoflush=False)
session = Session()

class Json(TypeDecorator):
    impl = String
    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)

class Variable(Base):
    __tablename__ = Path(__file__).stem
    name = Column(String(), primary_key=True)
    value = Column(Json())
    def __init__(self, name, value):
        self.name = name
        self.value = value

class Database():
    def __init__(self):
        Variable.__table__.create(checkfirst=True)

    def get(self, name: str, default=None):
        variable = self._query(name)
        if not variable:
            return default
        return variable.value
    
    def dump(self) -> dict:
        results = {}
        for variable in self._query():
            results[variable.name] = variable.value
        return results

    def add(self, name: str, value, overwrite=True) -> bool:
        variable = self._query(name)
        if variable:
            if not overwrite:
                return False
            self.remove(name)
        session.add(Variable(name, value))
        session.commit()
        return True
    
    def update(self, data: dict) -> bool:
        for key, value in data.items():
            self.add(key, value)
        return True

    def remove(self, name: str) -> bool:
        variable = self._query(name)
        if variable:
            session.delete(variable)
            session.commit()
            return True
        return False
    
    def clear(self, members: list=None) -> bool:
        data = self._query()
        if data:
            for variable in data:
                if members:
                    if variable.name not in members:
                        continue
                session.delete(variable)
            session.commit()
            return True
        return False

    def _query(self, name=None):
        if name:
            return session.query(Variable).filter_by(name=name).first()
        return session.query(Variable).all()