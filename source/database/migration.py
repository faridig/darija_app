import os
import json
import psycopg2
from dotenv import load_dotenv
from tqdm import tqdm

class PostgreSQLMigrator:
    """
    Classe pour migrer les données de traduction vers PostgreSQL.
    """
    
    def __init__(self):
        load_dotenv()
        self.conn = self._connect_to_db()
        self.cur = self.conn.cursor()
        
    def _connect_to_db(self):
        """Établit la connexion à la base de données PostgreSQL."""
        try:
            conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD'),
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT')
            )
            return conn
        except Exception as e:
            print(f"Erreur de connexion à la base de données: {e}")
            raise

    def create_tables(self):
        """Crée les tables nécessaires dans la base de données."""
        try:
            # Table des traductions
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id SERIAL PRIMARY KEY,
                    source_lang VARCHAR(10),
                    target_lang VARCHAR(10),
                    source_text TEXT,
                    target_text TEXT,
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des tags
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE
                )
            """)
            
            # Table de liaison traductions-tags
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS translation_tags (
                    translation_id INTEGER REFERENCES translations(id),
                    tag_id INTEGER REFERENCES tags(id),
                    PRIMARY KEY (translation_id, tag_id)
                )
            """)
            
            self.conn.commit()
            print("Tables créées avec succès")
            
        except Exception as e:
            print(f"Erreur lors de la création des tables: {e}")
            self.conn.rollback()
            raise

    def load_translations(self):
        """Charge les traductions depuis le fichier JSON."""
        try:
            with open('data/translations_with_tags.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement des traductions: {e}")
            raise

    def insert_translation(self, translation):
        """Insère une traduction dans la base de données."""
        try:
            self.cur.execute("""
                INSERT INTO translations (source_lang, target_lang, source_text, target_text, context)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                translation['source_lang'],
                translation['target_lang'],
                translation['source_text'],
                translation['target_text'],
                translation.get('context', '')
            ))
            return self.cur.fetchone()[0]
        except Exception as e:
            print(f"Erreur lors de l'insertion de la traduction: {e}")
            self.conn.rollback()
            raise

    def insert_tag(self, tag_name):
        """Insère un tag dans la base de données."""
        try:
            self.cur.execute("""
                INSERT INTO tags (name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            """, (tag_name,))
            result = self.cur.fetchone()
            if result:
                return result[0]
            # Si le tag existe déjà, récupérer son ID
            self.cur.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
            return self.cur.fetchone()[0]
        except Exception as e:
            print(f"Erreur lors de l'insertion du tag: {e}")
            self.conn.rollback()
            raise

    def link_translation_tag(self, translation_id, tag_id):
        """Lie une traduction à un tag."""
        try:
            self.cur.execute("""
                INSERT INTO translation_tags (translation_id, tag_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (translation_id, tag_id))
        except Exception as e:
            print(f"Erreur lors de la liaison traduction-tag: {e}")
            self.conn.rollback()
            raise

    def migrate(self):
        """Migre toutes les données vers PostgreSQL."""
        try:
            print("Début de la migration...")
            
            # Création des tables
            self.create_tables()
            
            # Chargement des traductions
            translations = self.load_translations()
            
            # Migration des données
            for translation in tqdm(translations, desc="Migration des traductions"):
                # Insertion de la traduction
                translation_id = self.insert_translation(translation)
                
                # Insertion des tags et création des liens
                for tag in translation.get('tags', []):
                    tag_id = self.insert_tag(tag)
                    self.link_translation_tag(translation_id, tag_id)
                
                # Sauvegarde intermédiaire tous les 100 enregistrements
                if translation_id % 100 == 0:
                    self.conn.commit()
            
            # Validation finale
            self.conn.commit()
            print("Migration terminée avec succès")
            
        except Exception as e:
            print(f"Erreur lors de la migration: {e}")
            self.conn.rollback()
            raise
        finally:
            self.cur.close()
            self.conn.close()

if __name__ == "__main__":
    migrator = PostgreSQLMigrator()
    migrator.migrate() 