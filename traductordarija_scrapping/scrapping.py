from playwright.sync_api import sync_playwright
import json
import time
import os

# Définition de la fonction de traduction
def traduire_texte_traductordarija(phrase, url="https://www.traductordarija.com/fr/"):
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
            
            # Prendre une capture d'écran de la page initiale
            page.screenshot(path="page_initiale.png")
            print("Capture d'écran initiale sauvegardée")

            # Remplir le textarea avec la phrase en français
            print("Remplissage du champ de texte...")
            page.fill('#text_to_translate', phrase)

            # Cliquer sur le bouton de traduction avec le bon sélecteur
            print("Clic sur le bouton de traduction...")
            # Utiliser le sélecteur correct pour le bouton
            page.click('button.btn.btn-primary[onclick="translateText()"]')
            
            # Attendre un peu pour voir ce qui se passe
            print("Attente de 5 secondes...")
            page.wait_for_timeout(5000)
            
            # Prendre une capture d'écran après le clic
            page.screenshot(path="apres_clic.png")
            print("Capture d'écran après clic sauvegardée")

            # Essayer plusieurs sélecteurs pour trouver le résultat
            print("Recherche du résultat avec différents sélecteurs...")
            selectors = [
                '#translation_result',
                '.translation-result',
                'textarea[name="translation_result"]',
                'textarea.result',
                'div.result textarea',
                'textarea:nth-child(2)'
            ]
            
            traduction = None
            for selector in selectors:
                try:
                    print(f"Essai du sélecteur : {selector}")
                    element = page.query_selector(selector)
                    if element:
                        print(f"Sélecteur trouvé : {selector}")
                        # Essayer différentes méthodes pour obtenir le texte
                        try:
                            traduction = element.input_value()
                            print(f"Valeur obtenue avec input_value() : '{traduction}'")
                            break
                        except:
                            try:
                                traduction = element.text_content()
                                print(f"Valeur obtenue avec text_content() : '{traduction}'")
                                break
                            except:
                                print("Impossible d'obtenir le texte de l'élément")
                except Exception as e:
                    print(f"Erreur avec le sélecteur {selector} : {str(e)}")
            
            # Si aucun sélecteur n'a fonctionné, essayer de récupérer tous les textarea
            if not traduction:
                print("Tentative de récupération de tous les textarea...")
                textareas = page.query_selector_all('textarea')
                print(f"Nombre de textarea trouvés : {len(textareas)}")
                for i, textarea in enumerate(textareas):
                    try:
                        value = textarea.input_value()
                        print(f"Textarea {i+1} : '{value}'")
                        # Si ce n'est pas le texte d'entrée, c'est probablement la traduction
                        if value != phrase:
                            traduction = value
                            print(f"Traduction probable trouvée : '{traduction}'")
                            break
                    except Exception as e:
                        print(f"Erreur avec textarea {i+1} : {str(e)}")
            
            # Prendre une capture d'écran finale
            page.screenshot(path="resultat_final.png")
            print("Capture d'écran finale sauvegardée")
            
            # Sauvegarder le HTML de la page pour analyse
            html = page.content()
            with open("page_html.txt", "w", encoding="utf-8") as f:
                f.write(html)
            print("HTML de la page sauvegardé")

            browser.close()
            
            if traduction:
                return traduction
            else:
                return "Traduction non trouvée"
    except Exception as e:
        print(f"Erreur lors de la traduction : {str(e)}")
        return f"Erreur: {str(e)}"

# Exemple d'utilisation :
if __name__ == "__main__":
    phrase = "Comment ça va aujourd'hui ?"
    print("Démarrage du script de traduction...")
    print(f"Répertoire de travail : {os.getcwd()}")
    traduction_darija = traduire_texte_traductordarija(phrase)
    print(f"Traduction en darija : {traduction_darija}")
    print("Script terminé")


