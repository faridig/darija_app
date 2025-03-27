import os
import json
from openai import OpenAI
from dotenv import load_dotenv

class RAGTranslationEnricher:
    """
    Cette classe lit deux fichiers JSON contenant des paires de traduction,
    les normalise en un format unique, utilise GPT-4 pour générer des tags et un contexte,
    puis enregistre le résultat. Pour des tests, on ne traite ici que 5 paires par fichier.
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

    def run(self):
        """
        1) Charge 5 paires depuis 'traductions_processed.json'
           et 5 paires depuis 'translations.json'.
        2) Concatène ces 10 paires.
        3) Pour chacune, appelle GPT-4 pour générer des tags et un contexte.
        4) Enregistre le résultat final dans 'final_translations_with_tags.json'.
        """

        processed_file = "../data_Darija-SFT-Mixture/darija_data/traductions_processed.json"
        scrapping_file = "../traductordarija_scrapping/translations.json"

        # Lecture et normalisation
        list_from_processed = self.load_traductions_processed(processed_file)
        list_from_scrapping = self.load_translations_scrapping(scrapping_file)

        # Tronquer à 5 paires max de chaque
        list_from_processed = list_from_processed[:5]
        list_from_scrapping = list_from_scrapping[:5]

        # Concaténer => 10 paires
        all_pairs = list_from_processed + list_from_scrapping
        print(f"Total de paires à analyser: {len(all_pairs)}")

        final_results = []
        for i, pair in enumerate(all_pairs, start=1):
            source_text = pair.get("source_text", "")
            target_text = pair.get("target_text", "")
            source_lang = pair.get("source_lang", "")
            target_lang = pair.get("target_lang", "")

            gen_result = self.generate_tags_and_context_gpt4(source_text, target_text)

            entry = {
                "id": f"pair_{i}",
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_text": source_text,
                "target_text": target_text,
                "tags": gen_result.get("tags", []),
                "context": gen_result.get("context", "")
            }
            final_results.append(entry)

        output_file = "final_translations_with_tags.json"
        with open(output_file, "w", encoding="utf-8") as out:
            json.dump(final_results, out, ensure_ascii=False, indent=2)

        print(f"Fichier de sortie créé: {output_file}")
        if final_results:
            print("Exemple de la première entrée enrichie :")
            # IMPORTANT: on ferme bien la parenthèse ici
            print(json.dumps(final_results[0], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    enricher = RAGTranslationEnricher()
    enricher.run()
