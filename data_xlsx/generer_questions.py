import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import time
import openpyxl

# Charger les variables d'environnement
load_dotenv()

class GenerateurQuestions:
    def __init__(self):
        """Initialise le client OpenAI."""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("La clé API OpenAI n'est pas définie dans le fichier .env")

    def generer_questions(self, langue: str, nombre_questions: int = 300) -> list:
        """
        Génère des questions touristiques dans la langue spécifiée.
        
        Args:
            langue: 'fr' pour français ou 'en' pour anglais
            nombre_questions: nombre de questions à générer
        
        Returns:
            Liste de questions/affirmations
        """
        questions = []
        batch_size = 20  # Nombre de questions par requête
        nombre_batches = (nombre_questions + batch_size - 1) // batch_size

        prompts = {
            'fr': """Génère {batch_size} questions ou affirmations différentes qu'un touriste français pourrait poser/dire au Maroc.
Les questions/affirmations doivent :
1. Être naturelles et à l'oral
2. Couvrir divers aspects (culture, transport, nourriture, logement, prix, directions, etc.)
3. Être variées dans leur formulation
4. Inclure des expressions courantes
5. Être courtes et directes

Format : Renvoie uniquement une liste de questions/affirmations, une par ligne.
""",
            'en': """Generate {batch_size} different questions or statements that an English-speaking tourist might ask/say in Morocco.
The questions/statements should:
1. Be natural and conversational
2. Cover various aspects (culture, transportation, food, accommodation, prices, directions, etc.)
3. Vary in their formulation
4. Include common expressions
5. Be short and direct

Format: Return only a list of questions/statements, one per line.
"""
        }

        for i in range(nombre_batches):
            print(f"\n🔄 Génération du batch {i+1}/{nombre_batches}")
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Vous êtes un expert en tourisme au Maroc."},
                        {"role": "user", "content": prompts[langue].format(batch_size=min(batch_size, nombre_questions - len(questions)))}
                    ],
                    temperature=0.8,
                    max_tokens=2000
                )
                
                # Extraire les questions de la réponse
                nouvelles_questions = response.choices[0].message.content.strip().split('\n')
                nouvelles_questions = [q.strip() for q in nouvelles_questions if q.strip()]
                questions.extend(nouvelles_questions)
                
                print(f"✅ {len(nouvelles_questions)} questions générées")
                
                # Attendre entre les requêtes
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Erreur lors de la génération : {str(e)}")
                continue

        return questions[:nombre_questions]

    def determiner_type(self, texte: str) -> str:
        """
        Détermine si le texte est une question ou une affirmation.
        
        Args:
            texte: Le texte à analyser
            
        Returns:
            'Question' ou 'Affirmation'
        """
        # Détection basée sur la ponctuation et les mots interrogatifs
        mots_interrogatifs = ['comment', 'pourquoi', 'quand', 'où', 'qui', 'quel', 'quelle', 'quels', 'quelles', 
                            'combien', 'est-ce', 'what', 'why', 'when', 'where', 'who', 'which', 'how', 'can', 'could']
        
        texte_lower = texte.lower()
        
        # Vérifier si c'est une question
        if ('?' in texte or
            any(texte_lower.startswith(mot) for mot in mots_interrogatifs) or
            any(f" {mot} " in texte_lower for mot in mots_interrogatifs)):
            return 'Question'
        
        return 'Affirmation'

    def sauvegarder_xlsx(self, questions: list, langue: str):
        """
        Sauvegarde les questions dans un fichier XLSX.
        
        Args:
            questions: Liste des questions à sauvegarder
            langue: 'fr' pour français ou 'en' pour anglais
        """
        noms_fichiers = {
            'fr': 'questions_fr_maroc.xlsx',
            'en': 'questions_en_morocco.xlsx'
        }
        
        # Créer le DataFrame
        df = pd.DataFrame({
            'id': range(1, len(questions) + 1),
            'Questions ou Affirmations': questions,
            'langue': [langue] * len(questions)
        })
        
        chemin_fichier = os.path.join(os.path.dirname(__file__), noms_fichiers[langue])
        
        # Sauvegarder en XLSX avec formatage
        with pd.ExcelWriter(chemin_fichier, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Questions')
            
            # Ajuster la largeur des colonnes
            worksheet = writer.sheets['Questions']
            worksheet.column_dimensions['A'].width = 10  # id
            worksheet.column_dimensions['B'].width = 60  # Questions ou Affirmations
            worksheet.column_dimensions['C'].width = 15  # langue
            
            # Ajouter un filtre automatique
            worksheet.auto_filter.ref = worksheet.dimensions
            
            # Formater l'en-tête
            for cell in worksheet[1]:
                cell.font = openpyxl.styles.Font(bold=True)
                cell.fill = openpyxl.styles.PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")
            
        print(f"\n✅ Questions et affirmations sauvegardées dans {noms_fichiers[langue]}")

def main():
    generateur = GenerateurQuestions()
    
    # Générer et sauvegarder les questions en français
    print("\n🇫🇷 Génération des questions en français...")
    questions_fr = generateur.generer_questions('fr')
    generateur.sauvegarder_xlsx(questions_fr, 'fr')
    
    # Générer et sauvegarder les questions en anglais
    print("\n🇬🇧 Génération des questions en anglais...")
    questions_en = generateur.generer_questions('en')
    generateur.sauvegarder_xlsx(questions_en, 'en')

if __name__ == "__main__":
    main() 