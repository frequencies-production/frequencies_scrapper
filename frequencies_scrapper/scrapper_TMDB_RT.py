import os
import sys
import time
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIG ===
API_KEY = '98dfa26ff29c129579068f12ca2048b3'
CHROMEDRIVER_PATH = 'c:\\Users\\schmi\\.cache\\selenium\\chromedriver\\win64\\135.0.7049.84\\chromedriver.exe'
NB_PAGES = 2

# === PHASE 1 : Récupération des films depuis TMDB ===
def fetch_tmdb_movies(api_key, pages=1):
    all_movies = []
    for page in range(1, pages + 1):
        url = 'https://api.themoviedb.org/3/discover/movie'
        params = {
            'api_key': api_key,
            'language': 'en-US',
            'sort_by': 'popularity.desc',
            'include_adult': 'false',
            'include_video': 'false',
            'page': page
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Erreur page {page}: {response.status_code}")
            continue

        results = response.json().get("results", [])
        for movie in results:
            all_movies.append({
                "id": movie["id"],
                "title": movie["title"],
                "release_date": movie.get("release_date", "")
            })
        time.sleep(0.3)
    return pd.DataFrame(all_movies)


def extract_rotten_tomatoes_scores(driver, url):
    try:
        driver.get(url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Scores
        try:
            script_tag = driver.find_element(By.ID, "media-scorecard-json")
            json_content = script_tag.get_attribute("innerHTML")
            score_data = json.loads(json_content)
            critic_score = score_data.get("criticsScore", {}).get("scorePercent", "")
            audience_score = score_data.get("audienceScore", {}).get("scorePercent", "")
        except:
            critic_score = ""
            audience_score = ""

        # Synopsis
        synopsis_tag = soup.select_one('[data-qa="synopsis-value"]')
        synopsis = synopsis_tag.text.strip() if synopsis_tag else ""

        # Initialisation des champs
        director = producers = genres = ""

        # Parse des infos dans les éléments "category-wrap"
        for category in soup.select('div.category-wrap'):
            label_tag = category.select_one('dt .key')
            value_tags = category.select('dd [data-qa="item-value"]')
            if not label_tag:
                continue

            label = label_tag.text.strip().lower()

            values = ", ".join([tag.text.strip() for tag in value_tags]) if value_tags else ""

            if "director" in label:
                director = values
            elif "producer" in label:
                producers = values
            elif "genre" in label:
                genres = values

        # Cast (top 5)
        cast_tags = soup.select('a[data-qa="cast-actor-link"]') or soup.select('a.cast-and-crew-item__actor')
        cast_list = [tag.text.strip() for tag in cast_tags[:5]]
        cast = ", ".join(cast_list)

        return critic_score, audience_score, synopsis, director, producers, genres, cast

    except Exception as e:
        print(f"[!] Erreur scraping {url} : {e}")
        return "", "", "", "", "", "", ""



# === PHASE 2 : Ajout des scores Rotten Tomatoes ===
def add_rottentomatoes_scores(df):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    # driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    critic_scores = []
    audience_scores = []
    synopses = []
    directors = []
    producers = []
    genres = []
    casts = []

    for index, row in df.iterrows():
        film_title = row["title"]
        print(f"🔍 Recherche : {film_title}")
        try:
            search_url = f"https://www.rottentomatoes.com/search?search={film_title.replace(' ', '%20')}"
            driver.get(search_url)
            time.sleep(2)

            try:
                link = driver.find_element(By.CSS_SELECTOR, 'search-page-result a[href*="/m/"]')
                film_url = link.get_attribute("href")

                critic, audience, synopsis, director, producer, genre, cast = extract_rotten_tomatoes_scores(driver, film_url)
                critic_scores.append(critic)
                audience_scores.append(audience)
                synopses.append(synopsis)
                directors.append(director)
                producers.append(producer)
                genres.append(genre)
                casts.append(cast)

                print(f"✅ {film_title} — Critic: {critic}%, Audience: {audience}%")

            except Exception as e:
                print(f"❌ Film non trouvé pour {film_title} : {e}")
                critic_scores.append("")
                audience_scores.append("")
                synopses.append("")
                directors.append("")
                producers.append("")
                genres.append("")
                casts.append("")

        except Exception as e:
            print(f"⛔ Erreur sur {film_title} : {e}")
            critic_scores.append("")
            audience_scores.append("")
            synopses.append("")
            directors.append("")
            producers.append("")
            genres.append("")
            casts.append("")

    driver.quit()
    df["RT_Critic_Score"] = critic_scores
    df["RT_Audience_Score"] = audience_scores
    df["RT_Synopsis"] = synopses
    df["RT_Director"] = directors
    df["RT_Producers"] = producers
    df["RT_Genres"] = genres
    df["RT_Cast"] = casts
    return df

# === Sauvegarde du DataFrame ===
def save_dataframe(df, mode="csv", output_name="films_test.csv", db_url=None, table_name="films"):
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_path = os.path.join(r"../csv/", output_name)

    if mode == "csv":
        try:
            df.to_csv(output_path, index=False, sep=";")
            print(f"✅ DataFrame sauvegardé dans le fichier CSV : {output_path}")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde CSV : {e}")
    elif mode == "db":
        if not db_url:
            raise ValueError("❌ db_url est requis pour le mode 'db'")
        try:
            engine = create_engine(db_url)
            df.to_sql(table_name, con=engine, if_exists='replace', index=False)
            print(f"✅ DataFrame sauvegardé dans la table '{table_name}' de la base.")
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde dans la base de données : {e}")
    else:
        raise ValueError("❌ Le paramètre 'mode' doit être 'csv' ou 'db'")

# === MAIN ===
def main():
    df_tmdb = fetch_tmdb_movies(API_KEY, pages=NB_PAGES)
    print(df_tmdb)

    df_final = add_rottentomatoes_scores(df_tmdb)
    print("final dataframe")
    print(df_final)

    save_dataframe(df_final)
    print("fin")

if __name__ == "__main__":
    main()
