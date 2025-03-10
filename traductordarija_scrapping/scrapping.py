from playwright.sync_api import sync_playwright
import json
import time
import os

# Définition de la fonction de traduction
def traduire_texte_traductordarija(phrase, url="https://www.learnmoroccan.com/fr/translator"):
    print(f"Tentative de traduction de : '{phrase}'")
    try:
        with sync_playwright() as p:
            print("Lancement du navigateur...")
            browser = p.chromium.launch(headless=False)  # Mode visible pour déboguer
            page = browser.new_page()

            # Ouvrir la page du traducteur
            print(f"Accès à l'URL : {url}")
            page.goto(url)
            print("Page chargée")
            
            # Gérer le bouton initial inversion de langue qui apparaît lors de la première ouverture
            try:
                print("Vérification de la présence du bouton initial d'inversion de langue...")
                # Utiliser un sélecteur plus précis basé sur les attributs fournis
                bouton_selector = "button.shadow-md.shadow-\\[rgba\\(0\\,0\\,0\\,0\\.01\\)\\].border.border-\\[\\#ECECEC\\].mx-2.p-\\[17px\\].rounded-2xl.bg-white.hover\\:bg-lighter.duration-150[aria-label='échanger les langues'][title='échanger les langues']"
                
                # Attendre que le bouton soit visible avec un timeout court
                page.wait_for_selector(bouton_selector, state="visible", timeout=5000)
                
                print("Bouton initial détecté, clic sur le bouton...")
                page.locator(bouton_selector).click()
                print("Bouton initial cliqué")
                
                # Ajouter un délai court pour s'assurer que l'action est traitée
                page.wait_for_timeout(1000)
            except Exception as e:
                print(f"Erreur lors de la gestion du bouton initial : {e}, poursuite du script")
            
            # Prendre une capture d'écran de la page initiale
            page.screenshot(path="page_initiale.png")
            print("Capture d'écran initiale sauvegardée")
            
            # Sélectionner la langue française depuis le menu déroulant
            print("Gestion du menu déroulant de sélection de langue...")
            
            # 1. Cliquer sur le sélecteur de langue pour ouvrir le menu déroulant
            print("Ouverture du menu déroulant de langues...")
            # Utiliser la syntaxe correcte pour les XPath avec Playwright
            page.locator("xpath=/html/body/div/div[2]/div[2]/div[1]/div[1]").click()
            # Attendre que le menu déroulant s'ouvre
            page.wait_for_timeout(1000)
            print("Menu déroulant ouvert")
            
            # 2. Sélectionner la langue française dans le menu déroulant
            print("Sélection de la langue française dans le menu...")
            # Utiliser un sélecteur qui cible spécifiquement l'option "Français" dans le menu déroulant
            page.locator("div:has-text('Français'):not(:has(div:has-text('Français')))").first.click()
            print("Langue française sélectionnée")
            
            # Ajouter un délai court pour s'assurer que la sélection est prise en compte
            page.wait_for_timeout(1000)
            
            # Activer le bouton toggle
            print("Activation du bouton toggle...")
            # Utiliser le XPath exact fourni par l'utilisateur avec la syntaxe correcte
            page.locator("xpath=/html/body/div/div[2]/div[3]/div/label/div/div").click()
            print("Bouton toggle activé")
            
            # Entrer le texte à traduire
            print(f"Saisie du texte : '{phrase}'")
            page.fill("textarea.pl-1.w-full.bg-white.outline-none.overflow-hidden.pt-2.resize-none.min-h-28.sm\\:min-h-48", phrase)
            
            # Cliquer sur le bouton de traduction
            print("Clic sur le bouton de traduction")
            page.locator("button.font-normal.shadow-sm.text-darkerlime.bg-lime.hover\\:bg-smoothlime.disabled\\:text-textGrey.transition.duration-150.disabled\\:bg-lightgrey.disabled\\:text-darkerlime.min-w-\\[130px\\].disabled\\:text-textGrey.p-3.px-8.flex.flex-row.gap-3.items-center.z-10.w-full.rounded-xl.justify-center.py-5.text-xl.font-normal.bg-blue-500.hover\\:bg-blue-600:has-text('Traduire')").click()
            
            # Ajouter un délai plus long après le clic sur le bouton de traduction
            print("Attente de 5 secondes pour laisser le temps au site de traiter la demande...")
            page.wait_for_timeout(5000)  # 5 secondes d'attente
            
            # Attendre que la traduction soit disponible
            print("Attente du résultat de la traduction...")
            page.wait_for_selector("xpath=/html/body/div/div[2]/div[4]/p[2]", state="visible", timeout=10000)
            
            # Récupérer le résultat de la traduction
            traduction = page.text_content("xpath=/html/body/div/div[2]/div[4]/p[2]")
            print(f"Traduction obtenue : {traduction}")
            
            # Récupérer également la version en caractères arabes si disponible
            try:
                traduction_arabe = page.text_content("xpath=/html/body/div/div[2]/div[4]/p[1]")
                print(f"Traduction en caractères arabes : {traduction_arabe}")
                # Combiner les deux traductions
                traduction_complete = {
                    "latin": traduction,
                    "arabic": traduction_arabe
                }
            except Exception as e:
                print(f"Impossible de récupérer la version en caractères arabes : {e}")
                traduction_complete = {
                    "latin": traduction,
                    "arabic": ""
                }
            
            # Prendre une capture d'écran du résultat
            page.screenshot(path="resultat_traduction.png")
            print("Capture d'écran du résultat sauvegardée")
            
            # Fermer le navigateur
            browser.close()
            
            return traduction_complete
    except Exception as e:
        print(f"Erreur lors de la traduction : {e}")
        return None


def sauvegarder_traduction_json(phrase, traduction, fichier_json="translations.json"):
    """
    Sauvegarde la traduction dans un fichier JSON structuré.
    
    Args:
        phrase (str): La phrase en français à traduire
        traduction (dict): Le résultat de la traduction (latin et arabic)
        fichier_json (str): Le chemin du fichier JSON où sauvegarder les traductions
    """
    # Créer l'entrée de traduction au format demandé
    nouvelle_traduction = {
        "source_lang": "fr",
        "source": phrase,
        "target_lang": "darija",
        "target": traduction["arabic"] if traduction["arabic"] else traduction["latin"]
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


# Exemple d'utilisation :
if __name__ == "__main__":
    phrase = "Comment ça va aujourd'hui ?"
    print("Démarrage du script de traduction...")
    print(f"Répertoire de travail : {os.getcwd()}")
    
    # Traduire la phrase
    traduction_darija = traduire_texte_traductordarija(phrase)
    
    if traduction_darija:
        print(f"Traduction en darija : {traduction_darija}")
        # Sauvegarder la traduction dans un fichier JSON
        sauvegarder_traduction_json(phrase, traduction_darija)
    else:
        print("La traduction a échoué")
    
    print("Script terminé")


