from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# --- Configuration du WebDriver ---
CHROMEDRIVER_PATH = r"c:\\Users\\schmi\\.cache\\selenium\\chromedriver\\win64\\135.0.7049.84\\chromedriver.exe"  # À adapter
service = Service(CHROMEDRIVER_PATH)
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(service=service, options=options)

# Liste pour stocker les résultats
films_data = []

try:
    url = "https://www.rottentomatoes.com/browse/movies_in_theaters/"
    driver.get(url)

    # attendre que les films soient visibles
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-qa="discovery-media-list-item-caption"]'))
    )

    # Accepter les cookies si nécessaire
    try:
        accept_button = driver.find_element(By.ID, "truste-consent-button")
        accept_button.click()
        time.sleep(2)
    except:
        pass

    # Récupérer tous les films
    movies = driver.find_elements(By.CSS_SELECTOR, '[data-qa="discovery-media-list-item-caption"]')

    for movie in movies[:30]:  # limite à 30 pour l'exemple
        try:
            title = movie.find_element(By.CSS_SELECTOR, '[data-qa="discovery-media-list-item-title"]').text.strip()

            # Date de sortie
            try:
                release_date = movie.find_element(By.CSS_SELECTOR, '[data-qa="discovery-media-list-item-start-date"]').text.strip()
            except:
                release_date = ""

            # Scores
            try:
                critics_score = movie.find_element(By.CSS_SELECTOR, 'rt-text[slot="criticsScore"]').text.strip()
            except:
                critics_score = ""

            try:
                audience_score = movie.find_element(By.CSS_SELECTOR, 'rt-text[slot="audienceScore"]').text.strip()
            except:
                audience_score = ""

            films_data.append({
                "Titre": title,
                "Date de sortie": release_date,
                "Score Critique": critics_score,
                "Score Audience": audience_score
            })

        except Exception as e:
            print(f"Erreur sur un film : {e}")
            continue

finally:
    driver.quit()

# --- Création DataFrame ---
df = pd.DataFrame(films_data)

# --- Export CSV ---
save_path = r"csv/films_rottentomatoes.csv"
df.to_csv(save_path, index=False, encoding="utf-8")

print(f"✅ Données enregistrées dans '{save_path}'")
