'''enrichir les traductions des deux fichiers "../data_Darija-SFT-Mixture/darija_data/traductions_processed.json" et "../traductordarija_scrapping/translations.json" avec des tags et un contexte'''

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm  # Pour la barre de progression

class RAGTranslationEnricher:
    """
    Cette classe lit deux fichiers JSON contenant des paires de traduction,
    les normalise en un format unique, utilise GPT-4 pour générer des tags et un contexte,
    puis enregistre le résultat.
    """

    def __init__(self):
        """
        Initialise la clé d'API OpenAI depuis les variables d'environnement.
        Vérifie que la clé existe, sinon lève une erreur.
        """
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "La clé API OpenAI n'est pas définie dans les variables d'environnement (.env). "
                "Assurez-vous d'avoir OPENAI_API_KEY=... dans votre fichier .env ou vos variables d'environnement."
            )
        self.client = OpenAI(api_key=api_key)

    def load_traductions_processed(self, filepath: str) -> list:
        """
        Lit 'traductions_processed.json' (format direction + pairs).

        Exemple de structure d'entrée :
        [
          {
            "direction": "fr_dr",
            "pairs": [
              {
                "texte_cible": "Que penses-tu des pommes de terre?",
                "traduction": "أشنو راإياك ف لبطاطا?"
              }
            ]
          },
          ...
        ]

        Retourne une liste de dictionnaires normalisés :
        [
          {
            "source_lang": "fr",
            "target_lang": "dr",
            "source_text": "Que penses-tu des pommes de terre?",
            "target_text": "أشنو راإياك ف لبطاطا?"
          },
          ...
        ]
        """
        if not os.path.isfile(filepath):
            print(f"Fichier introuvable: {filepath}")
            return []

        with open(filepath, "r", encoding="utf-8") as f:
            original_data = json.load(f)

        results = []
        for entry in original_data:
            direction = entry.get("direction", "")
            pairs = entry.get("pairs", [])

            if "_" in direction:
                source_lang, target_lang = direction.split("_", 1)
            else:
                source_lang, target_lang = "unknown", "unknown"

            for p in pairs:
                source_text = p.get("texte_cible", "")
                target_text = p.get("traduction", "")
                # On ajoute seulement s'il y a du contenu
                if source_text or target_text:
                    results.append({
                        "source_lang": source_lang,
                        "target_lang": target_lang,
                        "source_text": source_text,
                        "target_text": target_text
                    })
        return results

    def load_translations_scrapping(self, filepath: str) -> list:
        """
        Lit 'translations.json' (champ "translations") au format :
        {
          "translations": [
            {
              "source_lang": "fr",
              "source": "Tu connais un bon restaurant marocain dans le coin ?",
              "target_lang": "darija",
              "target": "تعرف شي مطعم..."
            },
            ...
          ]
        }

        Retourne une liste de dictionnaires normalisés :
        [
          {
            "source_lang": "fr",
            "target_lang": "dr",
            "source_text": "Tu connais un bon restaurant marocain dans le coin ?",
            "target_text": "تعرف شي مطعم..."
          },
          ...
        ]
        """
        if not os.path.isfile(filepath):
            print(f"Fichier introuvable: {filepath}")
            return []

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        translations_data = data.get("translations", [])
        results = []
        for t in translations_data:
            source_lang = t.get("source_lang", "")
            target_lang = t.get("target_lang", "")
            # Uniformisation : remplacer "darija" par "dr"
            if target_lang.lower() == "darija":
                target_lang = "dr"
            source_text = t.get("source", "")
            target_text = t.get("target", "")

            if source_text or target_text:
                results.append({
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "source_text": source_text,
                    "target_text": target_text
                })
        return results

    def generate_tags_and_context_gpt4(self, source_text: str, target_text: str) -> dict:
        """
        Utilise GPT-4 (ChatCompletion) pour produire un dictionnaire
        {
          "tags": [...],
          "context": "..."
        }
        basé sur une analyse du texte source et du texte cible.
        """

        system_message = {
            "role": "system",
            "content": (
                "Tu es un assistant IA expert en classification de texte et en analyse sémantique. "
                "Tu reçois deux textes : un texte source et sa traduction (texte cible). "
                "Ta mission est de générer, en utilisant une taxonomie contrôlée, entre 2 et 5 'tags' pertinents qui décrivent le contenu des textes. "
                "Ces tags doivent couvrir notamment : "
                "- le domaine ou sujet (ex. gastronomie, finance, médical, juridique, technologie, etc.), "
                "- le registre ou style (informel, formel, technique, littéraire, humoristique, etc.), "
                "- l'intention ou la fonction (question, affirmation, demande, excuse, conseil, etc.). "
                "Il est impératif de ne pas utiliser de tags relatifs aux langues (pas de 'dr', 'fr', 'eng', 'arabic', 'french', 'english'), "
                "car ces informations sont déjà disponibles ailleurs. \n\n"
                "Ensuite, tu dois produire un 'context' concis en français (1 à 2 phrases) qui décrit la situation d'usage de ces phrases, "
                "en te concentrant sur l'objectif ou l'intention sous-jacente, sans répéter les informations de langue. \n\n"
                "Important : \n"
                "- Les tags doivent être choisis parmi des catégories prédéfinies (domaine, style, intention) et ne doivent pas inclure d'indications de langue. \n"
                "- Retourne un objet JSON valide contenant uniquement les clés 'tags' et 'context'. \n"
                "- Ne rajoute pas d'autres commentaires, explications ou champs supplémentaires."
            )
        }
        user_message = {
            "role": "user",
            "content": f'Texte source: "{source_text}"\nTexte cible: "{target_text}"'
        }


        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[system_message, user_message],
                max_tokens=200,
                temperature=0.0
            )
            raw_output = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Erreur lors de l'appel à l'API GPT-4: {e}")
            return {"tags": [], "context": ""}

        try:
            result_json = json.loads(raw_output)
            return result_json
        except json.JSONDecodeError:
            print("Impossible de parser la sortie JSON du LLM. Sortie brute :")
            print(raw_output)
            return {"tags": [], "context": ""}

    def find_last_processed_pair(self, results: list) -> int:
        """
        Trouve l'index de la dernière paire traitée en analysant les IDs dans les résultats.
        Retourne -1 si aucun résultat n'existe.
        """
        if not results:
            return -1
            
        # Trouver le plus grand ID numérique dans les résultats
        max_id = -1
        for entry in results:
            try:
                # Extraire le numéro de l'ID (pair_123 ou pair_inverse_123)
                id_num = int(entry['id'].split('_')[-1])
                max_id = max(max_id, id_num)
            except (KeyError, ValueError, IndexError):
                continue
                
        return max_id

    def run(self):
        """
        1) Charge toutes les paires et le fichier existant
        2) Détecte automatiquement le point de reprise
        3) Continue le traitement à partir de ce point
        4) Enregistre le résultat final dans 'translations_with_tags.json'
        """
        processed_file = "../data_Darija-SFT-Mixture/darija_data/traductions_processed.json"
        scrapping_file = "../traductordarija_scrapping/translations.json"
        output_file = "translations_with_tags.json"

        print("Chargement des données...")
        # Charger les fichiers sources
        list_from_processed = self.load_traductions_processed(processed_file)
        list_from_scrapping = self.load_translations_scrapping(scrapping_file)
        all_pairs = list_from_processed + list_from_scrapping

        # Charger les résultats existants
        results = []
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    results = json.load(f)
                print(f"Fichier de résultats existant chargé avec {len(results)} entrées")
            except Exception as e:
                print(f"Erreur lors du chargement du fichier de résultats : {e}")
                print("Démarrage d'un nouveau traitement")
                results = []

        # Trouver le point de reprise
        last_pair_index = self.find_last_processed_pair(results)
        if last_pair_index == -1:
            print("Aucun résultat existant trouvé, démarrage depuis le début")
            last_pair_index = 0
        else:
            print(f"Reprise du traitement à partir de la paire {last_pair_index + 1}")

        print(f"Nombre de paires déjà traitées : {len(results)}")
        print(f"Total de paires à traiter : {len(all_pairs)}")

        # Continuer le traitement à partir de la dernière paire
        for i, pair in enumerate(tqdm(all_pairs[last_pair_index:], desc="Enrichissement des paires"), start=last_pair_index + 1):
            try:
                source_text = pair.get("source_text", "")
                target_text = pair.get("target_text", "")
                source_lang = pair.get("source_lang", "")
                target_lang = pair.get("target_lang", "")

                # Vérifier si la paire est valide
                if not source_text or not target_text:
                    print(f"\nPaire {i} ignorée : texte source ou cible vide")
                    continue

                # Générer les tags et le contexte une seule fois par paire
                gen_result = self.generate_tags_and_context_gpt4(source_text, target_text)

                # Paire originale
                original_entry = {
                    "id": f"pair_{i}",
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "source_text": source_text,
                    "target_text": target_text,
                    "tags": gen_result.get("tags", []),
                    "context": gen_result.get("context", "")
                }
                results.append(original_entry)

                # Paire inversée avec les mêmes tags et contexte
                inverse_entry = {
                    "id": f"pair_inverse_{i}",
                    "source_lang": target_lang,
                    "target_lang": source_lang,
                    "source_text": target_text,
                    "target_text": source_text,
                    "tags": gen_result.get("tags", []),  # Mêmes tags
                    "context": gen_result.get("context", "")  # Même contexte
                }
                results.append(inverse_entry)

                # Sauvegarde intermédiaire toutes les 50 paires
                if i % 50 == 0:
                    try:
                        with open(output_file, "w", encoding="utf-8") as out:
                            json.dump(results, out, ensure_ascii=False, indent=2)
                        print(f"\nSauvegarde intermédiaire effectuée après la paire {i}")
                    except Exception as e:
                        print(f"\nErreur lors de la sauvegarde intermédiaire : {e}")

            except Exception as e:
                print(f"\nErreur lors du traitement de la paire {i} : {e}")
                continue

        # Sauvegarde finale
        try:
            with open(output_file, "w", encoding="utf-8") as out:
                json.dump(results, out, ensure_ascii=False, indent=2)
            print(f"\nTraitement terminé ! Fichier mis à jour: {output_file}")
            print(f"Nombre total de paires : {len(results)}")
            
            if results:
                print("\nDernière paire traitée :")
                print(f"Direction: {results[-2]['source_lang']} → {results[-2]['target_lang']}")
                print(f"Tags: {results[-2]['tags']}")
                print(f"Context: {results[-2]['context']}")
        except Exception as e:
            print(f"\nErreur lors de la sauvegarde finale : {e}")

if __name__ == "__main__":
    enricher = RAGTranslationEnricher()
    enricher.run()
