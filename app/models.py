from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.database import db

class Sales(db.Model):
    __tablename__ = 'sales'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False)
    quantity = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'date': self.date.isoformat() if self.date else None,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Production(db.Model):
    __tablename__ = 'production'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False)
    quantity = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'date': self.date.isoformat() if self.date else None,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False)
    quantity = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'date': self.date.isoformat() if self.date else None,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Deficits(db.Model):
    __tablename__ = 'deficits'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False)
    quantity = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'date': self.date.isoformat() if self.date else None,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }