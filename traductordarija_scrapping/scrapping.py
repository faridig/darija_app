from playwright.sync_api import sync_playwright
import json
import time
import os
import pandas as pd

# Définition de la fonction de traduction
def traduire_texte_traductordarija(phrase, url_base="https://www.learnmoroccan.com/fr"):
    print(f"Tentative de traduction de : '{phrase}'")
    try:
        with sync_playwright() as p:
            print("Lancement du navigateur Chromium...")
            browser = p.chromium.launch(
                headless=False,    # Mode visible pour déboguer
                args=['--start-maximized']  # Démarrer en plein écran
            )
            page = browser.new_page(viewport={"width": 1920, "height": 1080})  # Définir une résolution HD
            
            # Commencer par la page d'accueil pour la connexion
            print("Accès à la page d'accueil pour connexion...")
            page.goto(url_base)
            page.wait_for_timeout(2000)
            
            # Se connecter
            print("Tentative de connexion...")
            if not se_connecter(page):
                print("La connexion a échoué, tentative de continuer quand même...")
            
            # Rediriger vers la page du traducteur
            url_traducteur = f"{url_base}/translator"
            print(f"Accès à la page du traducteur : {url_traducteur}")
            page.goto(url_traducteur)
            page.wait_for_timeout(2000)
            print("Page du traducteur chargée")
            
            # Prendre une capture d'écran initiale
            page.screenshot(path="04_page_traducteur.png")
            print("Capture d'écran du traducteur sauvegardée")
            
            # Gérer le bouton initial inversion de langue qui apparaît lors de la première ouverture
            try:
                print("Vérification de la présence du bouton initial d'inversion de langue...")
                bouton_selector = "button.shadow-md.shadow-\\[rgba\\(0\\,0\\,0\\,0\\.01\\)\\].border.border-\\[\\#ECECEC\\].mx-2.p-\\[17px\\].rounded-2xl.bg-white.hover\\:bg-lighter.duration-150[aria-label='échanger les langues'][title='échanger les langues']"
                
                page.wait_for_selector(bouton_selector, state="visible", timeout=5000)
                
                print("Bouton initial détecté, clic sur le bouton...")
                page.locator(bouton_selector).click()
                print("Bouton initial cliqué")
                
                page.wait_for_timeout(1000)
                page.screenshot(path="05_apres_bouton_initial.png")
            except Exception as e:
                print(f"Erreur lors de la gestion du bouton initial : {e}, poursuite du script")
            
            # Sélectionner la langue française depuis le menu déroulant
            print("Gestion du menu déroulant de sélection de langue...")
            
            # 1. Cliquer sur le sélecteur de langue pour ouvrir le menu déroulant
            print("Ouverture du menu déroulant de langues...")
            page.locator("xpath=/html/body/div/div[2]/div[2]/div[1]/div[1]").click()
            page.wait_for_timeout(1000)
            page.screenshot(path="06_menu_deroulant_ouvert.png")
            print("Menu déroulant ouvert")
            
            # 2. Sélectionner la langue française dans le menu déroulant
            print("Sélection de la langue française dans le menu...")
            page.locator("div:has-text('Français'):not(:has(div:has-text('Français')))").first.click()
            print("Langue française sélectionnée")
            
            page.wait_for_timeout(1000)
            page.screenshot(path="07_langue_francaise_selectionnee.png")
            
            # Activer le bouton toggle
            print("Activation du bouton toggle...")
            page.locator("xpath=/html/body/div/div[2]/div[3]/div/label/div/div").click()
            print("Bouton toggle activé")
            page.wait_for_timeout(1000)
            page.screenshot(path="08_toggle_active.png")
            
            # Entrer le texte à traduire
            print(f"Saisie du texte : '{phrase}'")
            page.fill("textarea.pl-1.w-full.bg-white.outline-none.overflow-hidden.pt-2.resize-none.min-h-28.sm\\:min-h-48", phrase)
            page.wait_for_timeout(1000)
            page.screenshot(path="09_texte_saisi.png")
            
            # Cliquer sur le bouton de traduction
            print("Clic sur le bouton de traduction")
            page.locator("button.font-normal.shadow-sm.text-darkerlime.bg-lime.hover\\:bg-smoothlime.disabled\\:text-textGrey.transition.duration-150.disabled\\:bg-lightgrey.disabled\\:text-darkerlime.min-w-\\[130px\\].disabled\\:text-textGrey.p-3.px-8.flex.flex-row.gap-3.items-center.z-10.w-full.rounded-xl.justify-center.py-5.text-xl.font-normal.bg-blue-500.hover\\:bg-blue-600:has-text('Traduire')").click()
            
            # Ajouter un délai plus long après le clic sur le bouton de traduction
            print("Attente de 8 secondes pour laisser le temps au site de traiter la demande...")
            page.wait_for_timeout(8000)  # 8 secondes d'attente
            page.screenshot(path="10_apres_traduction.png")
            
            # Récupérer directement la traduction en arabe avec un XPath précis
            print("Récupération directe de la traduction en arabe...")
            
            script_xpath_exact = """
            () => {
                try {
                    const xpath = "/html/body/div/div[2]/div[4]/p[2]";
                    const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    return result ? result.textContent : null;
                } catch (e) {
                    return "Erreur: " + e.message;
                }
            }
            """
            
            traduction_arabe = page.evaluate(script_xpath_exact)
            
            if traduction_arabe and not traduction_arabe.startswith("Erreur:") and traduction_arabe != "Marocain":
                print(f"Traduction trouvée avec le XPath exact : {traduction_arabe}")
            else:
                print(f"Le XPath exact a retourné : {traduction_arabe}")
                traduction_arabe = None
                
                # Si le XPath exact n'a pas fonctionné, essayer d'autres approches
                print("Tentative avec d'autres approches...")
                
                # Prendre une capture d'écran du HTML pour analyse
                html_content = page.content()
                with open("page_debug.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("HTML de la page sauvegardé pour analyse")
                
                # Récupérer tous les paragraphes pour analyse
                script_all_paragraphs = """
                () => {
                    const paragraphs = Array.from(document.querySelectorAll('p'));
                    return paragraphs.map((p, index) => {
                        return {
                            index: index,
                            text: p.textContent,
                            hasArabic: Array.from(p.textContent).some(c => c.charCodeAt(0) >= 0x0600 && c.charCodeAt(0) <= 0x06FF)
                        };
                    });
                }
                """
                
                all_paragraphs = page.evaluate(script_all_paragraphs)
                
                for p in all_paragraphs:
                    if p["hasArabic"] and p["text"] != "Marocain":
                        traduction_arabe = p["text"]
                        print(f"Traduction en arabe trouvée (paragraphe {p['index']}): {traduction_arabe}")
                        break
                
                if not traduction_arabe:
                    print("Aucune traduction trouvée dans l'analyse des paragraphes, essai avec d'autres XPath...")
                    
                    xpath_options = [
                        "/html/body/div/div[2]/div[4]/p[1]",
                        "//div[contains(@class, 'mt-4')]/p[1]",
                        "//div[contains(@class, 'mt-4')]/p[2]"
                    ]
                    
                    for xpath in xpath_options:
                        script_xpath = f"""
                        () => {{
                            try {{
                                const xpath = "{xpath}";
                                const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                                return result ? result.textContent : null;
                            }} catch (e) {{
                                return "Erreur: " + e.message;
                            }}
                        }}
                        """
                        
                        result = page.evaluate(script_xpath)
                        
                        if result and not result.startswith("Erreur:") and result != "Marocain" and any(ord(c) >= 0x0600 and ord(c) <= 0x06FF for c in result):
                            traduction_arabe = result
                            print(f"Traduction en arabe trouvée via XPath {xpath}: {traduction_arabe}")
                            break
                        else:
                            print(f"XPath {xpath} a retourné: {result}")
            
            # Prendre une capture d'écran finale
            page.screenshot(path="11_resultat_final.png")
            print("Capture d'écran finale sauvegardée")
            
            # Fermer le navigateur
            browser.close()
            
            return traduction_arabe
    except Exception as e:
        print(f"Erreur lors de la traduction : {e}")
        return None


def sauvegarder_traduction_json(phrase, traduction_arabe, fichier_json="translations.json"):
    """
    Sauvegarde la traduction dans un fichier JSON structuré.
    
    Args:
        phrase (str): La phrase en français à traduire
        traduction_arabe (str): La traduction en caractères arabes
        fichier_json (str): Le chemin du fichier JSON où sauvegarder les traductions
    """
    # Créer l'entrée de traduction au format demandé
    nouvelle_traduction = {
        "source_lang": "fr",
        "source": phrase,
        "target_lang": "darija",
        "target": traduction_arabe if traduction_arabe else "Traduction non disponible"
    }
    
    # Charger le fichier JSON existant s'il existe
    try:
        with open(fichier_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Créer une nouvelle structure si le fichier n'existe pas ou est invalide
        data = {"translations": []}
    
    # Ajouter la nouvelle traduction
    data["translations"].append(nouvelle_traduction)
    
    # Sauvegarder le fichier JSON
    with open(fichier_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Traduction sauvegardée dans {fichier_json}")


def se_connecter(page):
    """
    Effectue la connexion sur le site avec les identifiants fournis.
    
    Args:
        page: L'instance de page Playwright
    
    Returns:
        bool: True si la connexion a réussi, False sinon
    """
    try:
        # Cliquer sur le bouton "Se connecter"
        print("Clic sur le bouton 'Se connecter'...")
        page.locator("xpath=/html/body/header/div/div[2]/div/a[2]/button").click()
        page.wait_for_timeout(2000)
        page.screenshot(path="01_apres_clic_connexion.png")
        
        # Remplir l'identifiant
        print("Saisie de l'identifiant...")
        page.locator("xpath=/html/body/section[1]/div/form/div[1]/input").fill("faridigouti@gmail.com")
        page.wait_for_timeout(1000)
        
        # Remplir le mot de passe
        print("Saisie du mot de passe...")
        page.locator("xpath=/html/body/section[1]/div/form/div[2]/input").fill("34635263")
        page.wait_for_timeout(1000)
        page.screenshot(path="02_formulaire_rempli.png")
        
        # Cliquer sur le bouton de connexion
        print("Clic sur le bouton de validation...")
        page.locator("xpath=/html/body/section[1]/div/form/button").click()
        page.wait_for_timeout(3000)
        page.screenshot(path="03_apres_validation.png")
        
        return True
    except Exception as e:
        print(f"Erreur lors de la connexion : {e}")
        return False


def traduire_phrases_excel(chemin_fichier_excel):
    """
    Traduit toutes les phrases d'un fichier Excel.
    
    Args:
        chemin_fichier_excel (str): Chemin vers le fichier Excel contenant les phrases à traduire
    """
    try:
        print(f"Lecture du fichier Excel : {chemin_fichier_excel}")
        df = pd.read_excel(chemin_fichier_excel)
        
        nom_colonne = 'Questions ou Affirmations'
        if nom_colonne not in df.columns:
            raise ValueError(f"❌ La colonne '{nom_colonne}' n'existe pas dans le fichier Excel")
        
        print(f"✅ Utilisation de la colonne : {nom_colonne}")
        total_phrases = len(df)
        print(f"📊 Nombre total de phrases à traduire : {total_phrases}")
        
        # Définir le chemin du fichier JSON de sortie dans le dossier du script
        dossier_script = os.path.dirname(os.path.abspath(__file__))
        fichier_json = os.path.join(dossier_script, "translations.json")
        
        for index, row in df.iterrows():
            phrase = str(row[nom_colonne]).strip()
            if not phrase:
                continue
                
            print(f"\n🔄 Traduction {index + 1}/{total_phrases}")
            print(f"📝 Phrase source : {phrase}")
            
            traduction = traduire_texte_traductordarija(phrase)
            
            if traduction:
                print(f"✅ Traduction : {traduction}")
                sauvegarder_traduction_json(phrase, traduction, fichier_json)
            else:
                print(f"❌ Échec de la traduction pour : {phrase}")
            
            time.sleep(5)
            
        print("\n✅ Traduction terminée !")
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement : {str(e)}")


# Exemple d'utilisation :
if __name__ == "__main__":
    import argparse
    
    # Définir le chemin par défaut du fichier Excel
    FICHIER_EXCEL_PAR_DEFAUT = "../data_xlsx/questions_fr_affirmations_maroc.xlsx"
    
    parser = argparse.ArgumentParser(description='Script de traduction Français -> Darija')
    parser.add_argument('--excel', type=str, help='Chemin vers le fichier Excel à traduire', default=FICHIER_EXCEL_PAR_DEFAUT)
    parser.add_argument('--phrase', type=str, help='Phrase unique à traduire')
    args = parser.parse_args()
    
    print("Démarrage du script de traduction...")
    print(f"Répertoire de travail : {os.getcwd()}")
    
    if args.phrase:
        # Mode traduction phrase unique
        traduction_darija = traduire_texte_traductordarija(args.phrase)
        if traduction_darija:
            print(f"Traduction en darija : {traduction_darija}")
            sauvegarder_traduction_json(args.phrase, traduction_darija)
        else:
            print("La traduction a échoué")
    else:
        # Mode traduction depuis Excel (par défaut)
        fichier_excel = args.excel
        print(f"Utilisation du fichier Excel : {fichier_excel}")
        traduire_phrases_excel(fichier_excel)
    
    print("Script terminé")


