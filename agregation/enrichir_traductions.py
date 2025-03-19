import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List
import time

# Charger les variables d'environnement
load_dotenv()

class EnrichisseurTraductions:
    def __init__(self):
        """Initialise le client OpenAI et charge la clé API depuis les variables d'environnement."""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("La clé API OpenAI n'est pas définie dans le fichier .env")

    def enrichir_traduction(self, traduction: Dict) -> Dict:
        """
        Enrichit une traduction avec le domaine et le contexte en utilisant GPT.
        
        Args:
            traduction: Dictionnaire contenant la traduction à enrichir
            
        Returns:
            Dictionnaire enrichi avec le domaine et le contexte
        """
        prompt = f"""En tant qu'expert en darija (arabe marocain) et en culture marocaine, analysez cette traduction de manière concise :

Source ({traduction['source_lang']}): {traduction['source']}
Traduction (darija): {traduction['target']}

Fournissez les informations suivantes au format JSON :
1. domain: un seul mot pour le domaine principal (ex: cuisine, culture, transport, santé)
2. context: une seule phrase courte et précise décrivant la situation d'usage typique

Répondez uniquement en JSON avec cette structure exacte :
{{
    "domain": "string (un seul mot)",
    "context": "string (une seule phrase courte)"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Vous êtes un expert en darija et en culture marocaine."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Extraire et parser la réponse JSON
            metadata = json.loads(response.choices[0].message.content)
            
            # Ajouter les métadonnées à la traduction
            traduction_enrichie = traduction.copy()
            traduction_enrichie["domain"] = metadata["domain"]
            traduction_enrichie["context"] = metadata["context"]
            
            return traduction_enrichie
            
        except Exception as e:
            print(f"Erreur lors de l'enrichissement : {str(e)}")
            return traduction

    def traiter_fichier(self, chemin_entree: str, chemin_sortie: str):
        """
        Traite un fichier JSON contenant des traductions et sauvegarde les résultats enrichis.
        
        Args:
            chemin_entree: Chemin vers le fichier JSON source
            chemin_sortie: Chemin où sauvegarder le fichier JSON enrichi
        """
        try:
            # Charger les traductions
            with open(chemin_entree, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Enrichir chaque traduction
            traductions_enrichies = []
            total = len(data["translations"])
            
            for i, traduction in enumerate(data["translations"], 1):
                print(f"\n🔄 Traitement de la traduction {i}/{total}")
                print(f"Source: {traduction['source']}")
                
                # Enrichir la traduction
                traduction_enrichie = self.enrichir_traduction(traduction)
                
                # Afficher le domaine et le contexte
                print(f"\n📌 Domaine: {traduction_enrichie.get('domain', 'Non disponible')}")
                print(f"💡 Contexte: {traduction_enrichie.get('context', 'Non disponible')}")
                print("=" * 50)  # Ligne de séparation
                
                traductions_enrichies.append(traduction_enrichie)
                
                # Attendre un peu pour respecter les limites de l'API
                time.sleep(1)
                
            # Sauvegarder les résultats
            resultat = {"translations": traductions_enrichies}
            with open(chemin_sortie, 'w', encoding='utf-8') as f:
                json.dump(resultat, f, ensure_ascii=False, indent=2)
                
            print(f"\n✅ Traitement terminé ! Résultats sauvegardés dans {chemin_sortie}")
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement du fichier : {str(e)}")

if __name__ == "__main__":
    # Chemins des fichiers
    dossier_script = os.path.dirname(os.path.abspath(__file__))
    chemin_entree = os.path.join(dossier_script, "structured_translations.json")
    chemin_sortie = os.path.join(dossier_script, "translations_enrichies.json")
    
    # Créer et exécuter l'enrichisseur
    enrichisseur = EnrichisseurTraductions()
    enrichisseur.traiter_fichier(chemin_entree, chemin_sortie)