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
            
            # Gérer le bouton initial qui apparaît lors de la première ouverture
            try:
                print("Vérification de la présence du bouton initial...")
                # Utiliser un timeout court pour ne pas bloquer si le bouton n'est pas présent
                if page.locator("/html/body/div/div[2]/div[2]/button").count() > 0:
                    print("Bouton initial détecté, clic sur le bouton...")
                    page.locator("/html/body/div/div[2]/div[2]/button").click()
                    print("Bouton initial cliqué")
                else:
                    print("Bouton initial non détecté, poursuite du script")
            except Exception as e:
                print(f"Erreur lors de la gestion du bouton initial : {e}, poursuite du script")
            
            # Prendre une capture d'écran de la page initiale
            page.screenshot(path="page_initiale.png")
            print("Capture d'écran initiale sauvegardée")
            
            # Sélectionner la langue marocain
            print("Sélection de la langue marocaine...")
            page.locator("div.text-sm.sm\\:text-base:has-text('Marocain')").click()
            print("Langue marocaine sélectionnée")
            
            # Activer le bouton toggle
            print("Activation du bouton toggle...")
            # Utiliser le XPath exact fourni par l'utilisateur
            page.locator("/html/body/div/div[2]/div[3]/div/label/div/div").click()
            print("Bouton toggle activé")
            
            # Entrer le texte à traduire
            print(f"Saisie du texte : '{phrase}'")
            page.fill("textarea.pl-1.w-full.bg-white.outline-none.overflow-hidden.pt-2.resize-none.min-h-28.sm\\:min-h-48", phrase)
            
            # Cliquer sur le bouton de traduction
            print("Clic sur le bouton de traduction")
            page.locator("button.font-normal.shadow-sm.text-darkerlime.bg-lime.hover\\:bg-smoothlime.disabled\\:text-textGrey.transition.duration-150.disabled\\:bg-lightgrey.disabled\\:text-darkerlime.min-w-\\[130px\\].disabled\\:text-textGrey.p-3.px-8.flex.flex-row.gap-3.items-center.z-10.w-full.rounded-xl.justify-center.py-5.text-xl.font-normal.bg-blue-500.hover\\:bg-blue-600:has-text('Traduire')").click()
            
            # Attendre que la traduction soit disponible
            print("Attente du résultat de la traduction...")
            page.wait_for_selector("/html/body/div/div[2]/div[4]/p[2]", state="visible", timeout=10000)
            
            # Récupérer le résultat de la traduction
            traduction = page.text_content("/html/body/div/div[2]/div[4]/p[2]")
            print(f"Traduction obtenue : {traduction}")
            
            # Récupérer également la version en caractères arabes si disponible
            try:
                traduction_arabe = page.text_content("/html/body/div/div[2]/div[4]/p[1]")
                print(f"Traduction en caractères arabes : {traduction_arabe}")
                # Combiner les deux traductions
                traduction_complete = f"{traduction}\n{traduction_arabe}"
            except Exception as e:
                print(f"Impossible de récupérer la version en caractères arabes : {e}")
                traduction_complete = traduction
            
            # Prendre une capture d'écran du résultat
            page.screenshot(path="resultat_traduction.png")
            print("Capture d'écran du résultat sauvegardée")
            
            # Fermer le navigateur
            browser.close()
            
            return traduction_complete
    except Exception as e:
        print(f"Erreur lors de la traduction : {e}")
        return None


# Exemple d'utilisation :
if __name__ == "__main__":
    phrase = "Comment ça va aujourd'hui ?"
    print("Démarrage du script de traduction...")
    print(f"Répertoire de travail : {os.getcwd()}")
    traduction_darija = traduire_texte_traductordarija(phrase)
    print(f"Traduction en darija : {traduction_darija}")
    print("Script terminé")


