from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

OMDB_API_KEY = 'bb1856c2'

def search_movies(query):
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={query}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('Search', [])
    return []

def get_movie_details(imdb_id):
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    movies = search_movies(query)
    return jsonify(movies)

@app.route('/play/<imdb_id>')
def play(imdb_id):
    movie_details = get_movie_details(imdb_id)
    return render_template('play.html', imdb_id=imdb_id, movie_details=movie_details)

if __name__ == '__main__':
    app.run(debug=True)