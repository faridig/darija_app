import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, length, col, to_json
import pandas as pd
import json
import ast
from typing import List, Dict
import re
import logging
from collections import defaultdict

# Charger les variables d'environnement
load_dotenv()

# Vérifier si les identifiants Azure sont bien définis
storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
container_name = os.getenv("AZURE_CONTAINER_NAME")
parquet_folder = "data/"

if not storage_account_name or not storage_account_key or not container_name:
    raise ValueError("❌ ERREUR : Vérifie que les variables AZURE_STORAGE_ACCOUNT_NAME, AZURE_STORAGE_ACCOUNT_KEY et AZURE_CONTAINER_NAME sont bien définies dans .env.")

# Chemin vers les fichiers JAR Hadoop et Azure
hadoop_jars_path = os.path.expanduser("~/hadoop_jars")

# Liste des JARs nécessaires
jars = [
    f"{hadoop_jars_path}/hadoop-azure-3.3.1.jar",
    f"{hadoop_jars_path}/azure-storage-8.6.6.jar",
    f"{hadoop_jars_path}/jetty-util-9.4.40.v20210413.jar",
    f"{hadoop_jars_path}/jetty-util-ajax-9.4.40.v20210413.jar"
]

# Configuration Spark optimisée avec plus de mémoire
spark = SparkSession.builder \
    .appName("AzureParquetAnalysis") \
    .master("local[*]") \
    .config("spark.jars", ",".join(jars)) \
    .config("spark.hadoop.fs.azure", "org.apache.hadoop.fs.azure.NativeAzureFileSystem") \
    .config(f"spark.hadoop.fs.azure.account.key.{storage_account_name}.blob.core.windows.net", storage_account_key) \
    .config("spark.hadoop.fs.azure.account.auth.type", "SharedKey") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.driver.maxResultSize", "2g") \
    .config("spark.driver.host", "localhost") \
    .getOrCreate()

print("✅ PySpark est bien configuré avec les fichiers JAR pour Azure !")

# Ajouter les patterns regex au début du fichier, après les imports
TRANSLATION_PATTERNS = {
    "fr_dr": re.compile(r'\"content\":\"ترجم من الفرنساوية للدارجة:\\\\n(.*?)\".*?\"content\":\"(.*?)\"'),
    "dr_fr": re.compile(r'\"content\":\"(?:ترجم من الدارجة للفرنساوية:|ترجم:)\\\\n?(.*?)\".*?\"content\":\"(.*?)\"'),
    "en_dr": re.compile(r'\"content\":\"ترجم من الإنجليزية للدارجة:\\\\n(.*?)\".*?\"content\":\"(.*?)\"'),
    "dr_en": re.compile(r'\"content\":\"(?:ترجم من الدارجة للإنجليزية:|ترجم:)\\\\n?(.*?)\".*?\"content\":\"(.*?)\"')
}

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation_parsing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Statistiques globales pour le logging
parsing_stats = {
    "total_messages": 0,
    "matched_messages": 0,
    "unmatched_messages": 0,
    "matches_by_direction": defaultdict(int),
    "unmatched_details": []  # Nouvelle structure pour les détails
}

def load_and_filter_data():
    """Charge et filtre les données depuis Azure Blob Storage."""
    # URL du stockage Azure
    azure_url = f"wasbs://{container_name}@{storage_account_name}.blob.core.windows.net/{parquet_folder}"
    print(f"📂 Lecture des fichiers Parquet depuis : {azure_url}")
    
    # Lecture des données
    df = spark.read.parquet(azure_url)
    print("✅ Lecture réussie !")

    # 1. Réduire le nombre de partitions
    df_optimise = df.coalesce(4)

    # 2. Définir les directions à conserver
    directions_a_garder = ['dr_fr', 'fr_dr', 'en_dr', 'dr_en']

    # 3. Optimisation du filtrage avec cache
    df_filtre = df_optimise \
        .select('dataset', 'id', 'messages', 'direction') \
        .filter(col('direction').isin(directions_a_garder)) \
        .repartition(4, 'direction') \
        .persist()

    # 4. Créer le DataFrame plat avec messages_json
    df_plat = df_filtre \
        .withColumn("messages_json", to_json(col("messages"))) \
        .drop("messages") \
        .select("dataset", "id", "messages_json", "direction") \
        .toPandas()

    print(f"📊 Nombre de lignes : {len(df_plat):,}")
    print("\n📊 Distribution des directions :")
    print(df_plat['direction'].value_counts())

    return df_plat

# Dictionnaire direction → langues
DIRECTION_MAPPING = {
    "en_dr": ("en", "darija"),
    "fr_dr": ("fr", "darija"),
    "dr_fr": ("darija", "fr"),
    "dr_en": ("darija", "en")
}

def parse_messages(messages_str: str) -> List[Dict[str, str]]:
    """
    Parse les messages JSON en une liste de dictionnaires en utilisant des regex
    pour extraire directement les paires de traduction.
    """
    try:
        processed_messages = []
        message_matched = False
        parsing_stats["total_messages"] += 1
        
        # Pour chaque direction possible
        for direction, pattern in TRANSLATION_PATTERNS.items():
            # Chercher toutes les correspondances dans le texte
            matches = pattern.finditer(messages_str)
            matches_found = False
            
            for match in matches:
                matches_found = True
                message_matched = True
                source_text = match.group(1).strip()
                target_text = match.group(2).strip()
                
                # Nettoyer les caractères d'échappement JSON
                source_text = source_text.replace('\\n', '\n').replace('\\\"', '"').replace('\\\\', '\\')
                target_text = target_text.replace('\\n', '\n').replace('\\\"', '"').replace('\\\\', '\\')
                
                # Enlever les balises <|assistant|> si présentes
                target_text = re.sub(r'<\|assistant\|>', '', target_text).strip()
                
                if source_text and target_text:
                    parsing_stats["matches_by_direction"][direction] += 1
                    processed_messages.extend([
                        {"role": "user", "content": source_text, "direction": direction},
                        {"role": "assistant", "content": target_text}
                    ])
                    logging.debug(f"Match trouvé pour {direction}:")
                    logging.debug(f"Source: {source_text[:100]}...")
                    logging.debug(f"Target: {target_text[:100]}...")
        
        if not message_matched:
            parsing_stats["unmatched_messages"] += 1
            # Stocker les détails complets du message non matché
            try:
                # Essayer de parser le JSON pour une meilleure analyse
                message_data = json.loads(messages_str)
                unmatched_detail = {
                    "raw_message": messages_str[:1000],  # Premiers 1000 caractères
                    "parsed_structure": message_data,
                    "potential_issues": []
                }
                
                # Analyser les problèmes potentiels
                if "content" not in str(message_data):
                    unmatched_detail["potential_issues"].append("Pas de champ 'content' trouvé")
                if "ترجم" not in str(message_data):
                    unmatched_detail["potential_issues"].append("Pas d'instruction de traduction trouvée")
                if "\\n" not in str(message_data):
                    unmatched_detail["potential_issues"].append("Pas de retour à la ligne trouvé")
                
                parsing_stats["unmatched_details"].append(unmatched_detail)
                
            except json.JSONDecodeError:
                # Si le parsing JSON échoue, stocker le message brut
                parsing_stats["unmatched_details"].append({
                    "raw_message": messages_str[:1000],
                    "error": "Invalid JSON format",
                    "potential_issues": ["Format JSON invalide"]
                })
            
            logging.warning(f"Aucun match trouvé pour le message: {messages_str[:100]}...")
        else:
            parsing_stats["matched_messages"] += 1
        
        return processed_messages

    except Exception as e:
        logging.error(f"❌ Erreur lors du parsing des messages : {str(e)}")
        parsing_stats["unmatched_details"].append({
            "raw_message": messages_str[:1000],
            "error": str(e),
            "potential_issues": ["Erreur lors du traitement"]
        })
        return []

def print_parsing_stats():
    """
    Affiche et enregistre les statistiques de parsing.
    """
    logging.info("\n=== Statistiques de Parsing ===")
    logging.info(f"Messages totaux traités: {parsing_stats['total_messages']}")
    logging.info(f"Messages matchés: {parsing_stats['matched_messages']}")
    logging.info(f"Messages non matchés: {parsing_stats['unmatched_messages']}")
    logging.info("\nMatches par direction:")
    for direction, count in parsing_stats["matches_by_direction"].items():
        logging.info(f"- {direction}: {count}")
    
    logging.info("\nExemples de messages non matchés:")
    for i, sample in enumerate(parsing_stats["unmatched_details"], 1):
        logging.info(f"\n{i}. {sample['raw_message'][:100]}...")

def clean_translations(df: pd.DataFrame):
    """
    Nettoie et structure les traductions à partir du DataFrame.
    """
    valid_data = []
    invalid_data = []
    cleaned_count = 0
    quality_issues = []
    messages_with_multiple_pairs = 0
    multi_turns_count = 0

    # Liste des réponses courtes acceptables
    SHORT_ANSWERS = {
        "fr": ["oui", "non", "ah", "oh", "nan", "si"],
        "darija": ["أه", "لا", "أُه", "أُ", "نعم", "نع"]
    }

    for index, row in df.iterrows():
        try:
            # Utilisation de la colonne "messages_json" à la place de "messages"
            messages = parse_messages(row["messages_json"])
            direction = row.get("direction")

            # Vérifier la validité des messages
            if not messages or len(messages) < 2:
                invalid_data.append({
                    "index": index,
                    "reason": "Invalid message format",
                    "messages": row["messages_json"]
                })
                continue

            # Vérifier la validité de la direction
            if direction not in DIRECTION_MAPPING:
                invalid_data.append({
                    "index": index,
                    "reason": "Unknown direction value",
                    "direction": direction,
                    "messages": messages
                })
                continue

            source_lang, target_lang = DIRECTION_MAPPING[direction]
            
            # Traiter les paires de messages
            conversation_pairs = []
            for i in range(0, len(messages), 2):
                if i + 1 >= len(messages):
                    break
                    
                user_msg = messages[i]
                assistant_msg = messages[i + 1]
                
                if user_msg.get("role") != "user" or assistant_msg.get("role") != "assistant":
                    continue

                original_text = user_msg["content"].strip()
                translation_text = assistant_msg["content"].strip()

                # Vérifications de qualité
                quality_checks = []
                
                # 1. Vérifier la longueur minimale
                if len(original_text) < 2 or len(translation_text) < 2:
                    quality_checks.append("Texte trop court")
                
                # 2. Vérifier si la traduction est vide
                if not translation_text or translation_text.isspace():
                    quality_checks.append("Traduction vide")
                
                # 3. Vérifier si la traduction est identique à l'original
                if original_text == translation_text:
                    quality_checks.append("Traduction identique à l'original")
                
                # 4. Vérifier la longueur relative
                if len(translation_text) < len(original_text) * 0.3:
                    quality_checks.append("Traduction trop courte")
                
                # 5. Vérifier les caractères selon la direction
                if direction == "fr_dr" or direction == "en_dr":
                    arabic_chars = set("ابتثجحخدذرزسشصضطظعغفقكلمنهويءؤئأإآة")
                    non_arabic = [c for c in translation_text if c not in arabic_chars and not c.isspace() and not c.isdigit() and c not in ".,،!؟:؛()[]{}"]
                    if non_arabic:
                        quality_checks.append(f"Caractères non-arabes : {''.join(non_arabic)}")
                
                # Ajouter les informations de tour
                total_turns = len(messages) // 2
                current_turn = (i // 2) + 1
                quality_checks.append(f"Tour {current_turn}/{total_turns}")

                # Ajouter la paire à la conversation
                conversation_pairs.append({
                    "source_text": original_text,
                    "target_text": translation_text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "direction": direction,
                    "quality_checks": quality_checks,
                    "turn": current_turn,
                    "total_turns": total_turns
                })
                cleaned_count += 1

            # Ajouter toutes les paires de la conversation
            valid_data.extend(conversation_pairs)

            # Mettre à jour les statistiques
            if len(messages) > 2:
                messages_with_multiple_pairs += 1
                multi_turns_count += (len(messages) // 2) - 1

        except Exception as e:
            print(f"❌ Erreur lors du traitement de l'index {index}: {str(e)}")
            invalid_data.append({
                "index": index,
                "reason": f"Processing error: {str(e)}",
                "messages": row["messages_json"]
            })

    print(f"\n📊 Statistiques des conversations multi-tours :")
    print(f"- Total des traductions : {cleaned_count}")
    print(f"- Messages avec plusieurs paires : {messages_with_multiple_pairs}")
    print(f"- Nombre total de tours supplémentaires : {multi_turns_count}")
    if messages_with_multiple_pairs > 0:
        print(f"- Nombre moyen de paires par message multi-tour : {cleaned_count/messages_with_multiple_pairs:.2f}")

    return valid_data, invalid_data, cleaned_count, quality_issues

def save_json(data, filename: str):
    """Sauvegarde les données dans un fichier JSON avec encodage UTF-8."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def structure_translations(cleaned_file: str, output_file: str):
    """
    Transforme le JSON nettoyé en un format structuré explicite 
    avec les champs 'source_lang', 'source', 'target_lang' et 'target'.
    """
    with open(cleaned_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    structured_translations = []
    for item in data.get("translations", []):
        structured_translations.append({
            "source_lang": item.get("source_lang"),
            "source": item.get("source_text"),
            "target_lang": item.get("target_lang"),
            "target": item.get("target_text"),
            "direction": item.get("direction"),
            "quality_checks": item.get("quality_checks", []),
            "turn": item.get("turn", 1),
            "total_turns": item.get("total_turns", 1)
        })

    # Afficher les statistiques sur les conversations multi-tours
    multi_turn_conversations = sum(1 for t in structured_translations if t["total_turns"] > 1)
    total_turns = sum(t["turn"] for t in structured_translations)
    max_turns = max(t["total_turns"] for t in structured_translations) if structured_translations else 0

    print(f"\n📊 Statistiques des conversations structurées :")
    print(f"- Total des traductions : {len(structured_translations)}")
    print(f"- Conversations multi-tours : {multi_turn_conversations}")
    print(f"- Nombre total de tours : {total_turns}")
    print(f"- Nombre maximum de tours dans une conversation : {max_turns}")

    save_json({"translations": structured_translations}, output_file)

def save_to_csv(df: pd.DataFrame, output_dir: str):
    """Sauvegarde le DataFrame en format CSV."""
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "translations.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"✅ DataFrame sauvegardé en CSV dans : {csv_path}")

def save_unmatched_details(output_file: str):
    """
    Sauvegarde les détails des messages non matchés dans un fichier JSON.
    """
    unmatched_data = {
        "statistics": {
            "total_messages": parsing_stats["total_messages"],
            "matched_messages": parsing_stats["matched_messages"],
            "unmatched_messages": parsing_stats["unmatched_messages"],
            "matches_by_direction": dict(parsing_stats["matches_by_direction"])
        },
        "unmatched_details": parsing_stats["unmatched_details"]
    }
    
    save_json(unmatched_data, output_file)
    print(f"\n💾 Détails des messages non matchés sauvegardés dans : {output_file}")

if __name__ == "__main__":
    print("🚀 Démarrage du traitement des données...")
    
    # Charger et filtrer les données depuis Azure
    print("\n📥 Chargement des données depuis Azure...")
    merged_df = load_and_filter_data()
    
    # Sauvegarder en CSV
    csv_output_dir = "/projets/darija_app/data_Darija-SFT-Mixture/darija_data/csv_files"
    print("\n💾 Sauvegarde du DataFrame en CSV...")
    save_to_csv(merged_df, csv_output_dir)
    
    print("\n🧹 Nettoyage des données...")
    valid_data, invalid_data, cleaned_count, quality_issues = clean_translations(merged_df)

    # Afficher les statistiques de parsing
    print_parsing_stats()

    # Obtenir le chemin du dossier courant (agregation)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Créer le dossier structured_json s'il n'existe pas
    structured_json_dir = os.path.join(current_dir, "structured_json")
    os.makedirs(structured_json_dir, exist_ok=True)

    # Définir les chemins des fichiers de sortie dans le dossier structured_json
    cleaned_file = os.path.join(structured_json_dir, "cleaned_translations.json")
    invalid_file = os.path.join(structured_json_dir, "invalid_translations.json")
    structured_file = os.path.join(structured_json_dir, "structured_translations.json")
    quality_file = os.path.join(structured_json_dir, "quality_issues.json")
    unmatched_file = os.path.join(structured_json_dir, "unmatched_messages.json")

    print("\n💾 Sauvegarde des résultats...")
    save_json({"translations": valid_data}, cleaned_file)
    save_json(invalid_data, invalid_file)
    save_json(quality_issues, quality_file)

    print(f"\n✅ Nettoyage terminé ! {cleaned_count} entrées nettoyées et conservées.")
    print(f"⚠️ {len(invalid_data)} entrées bruitées détectées et enregistrées dans {invalid_file}")
    print(f"⚠️ {len(quality_issues)} problèmes de qualité détectés et enregistrés dans {quality_file}")

    if invalid_data:
        print("\n🔎 Exemples d'erreurs détectées :")
        for error in invalid_data[:5]:
            print(f"- Index {error['index']} : {error['reason']}")
            print(f"  Messages : {error['messages']}\n")

    # Structuration finale des traductions nettoyées
    print("\n🔄 Structuration finale des données...")
    structure_translations(cleaned_file, structured_file)

    # Sauvegarder les détails des messages non matchés
    save_unmatched_details(unmatched_file)

    print("\n✨ Traitement terminé avec succès !")

    # Arrêter la session Spark
    spark.stop()
