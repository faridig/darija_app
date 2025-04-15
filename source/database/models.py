from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Table, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Création du modèle de base
Base = declarative_base()

class Translation(Base):
    __tablename__ = 'translations'
    
    # Garder l'ID original comme une chaîne
    id = Column(String(50), primary_key=True)  # Pour préserver pair_XXXX
    source_lang = Column(String(10), nullable=False)
    target_lang = Column(String(10), nullable=False)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    # Stocker les tags directement comme un tableau
    tags = Column(ARRAY(String))
    context = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Contrainte pour éviter les doublons
    __table_args__ = (
        UniqueConstraint('source_text', 'target_text', name='uix_1'),
    )

def get_db_session():
    """Crée et retourne une session de base de données"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("L'URL de la base de données n'est pas définie dans les variables d'environnement")
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()

def init_db():
    """Initialise la base de données"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("L'URL de la base de données n'est pas définie dans les variables d'environnement")
    
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    print("Base de données initialisée avec succès!") 