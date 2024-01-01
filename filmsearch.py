import requests
import os

TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_URL = os.getenv('TMDB_URL')

headers = {
    "accept": "applcation/json",
    "Authorization": f"Bearer {TMDB_API_KEY}"
}


class MovieSearch:
    def search_api(self, title):
        search = {
            "query": title,
        }
        response = requests.get(TMDB_URL, headers=headers, params=search)
        data = response.json()
        return data

    def more_details(self, title_id):
        response = requests.get(f"https://api.themoviedb.org/3/movie/{title_id}", headers=headers)
        data = response.json()
        return data
