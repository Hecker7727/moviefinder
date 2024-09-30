from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import requests  # To make API requests
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Used for session management

# In-memory user credentials and watchlist for demo purposes (no database)
users = {
    'testuser': 'testpassword',
    'bldjack': 'password123'  # Example user
}
watchlist = {}

# Helper function to check login status
def is_logged_in():
    return 'username' in session

# Fetch random featured movies from OMDB
def get_featured_movies():
    # Example IDs for featured movies
    featured_ids = ['tt0111161', 'tt0133093', 'tt0137523', 'tt0241527', 'tt0298148', 'tt0372784', 'tt0468569', 'tt0816692']  # Random movie IDs
    random.shuffle(featured_ids)
    featured_movies = []
    for imdb_id in featured_ids[:3]:  # Get 3 random movies
        response = requests.get(f'http://www.omdbapi.com/?i={imdb_id}&apikey=bb1856c2')
        if response.status_code == 200:
            movie_data = response.json()
            if movie_data and movie_data.get('Response') == 'True':
                featured_movies.append(movie_data)
    return featured_movies

# Fetch actor images from OMDB
def get_actor_images(actors):
    actor_images = {}
    for actor in actors.split(','):
        actor = actor.strip()
        response = requests.get(f'http://www.omdbapi.com/?t={actor}&apikey=bb1856c2')
        if response.status_code == 200:
            actor_data = response.json()
            if actor_data and actor_data.get('Response') == 'True':
                actor_images[actor] = actor_data.get('Poster', '')
    return actor_images

# Homepage route (Index)
@app.route('/')
def index():
    if is_logged_in():
        username = session['username']
        featured_movies = get_featured_movies()  # Fetch featured movies
        return render_template('index.html', username=username, featured_movies=featured_movies)
    return redirect(url_for('login'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Register new user
        users[username] = password
        session['username'] = username  # Log user in after registration
        return redirect(url_for('index'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if user exists and password matches
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Movie Search Route
@app.route('/search', methods=['GET'])
def search():
    if is_logged_in():
        query = request.args.get('query')
        movies = []
        recommendations = []
        if query:
            response = requests.get(f'http://www.omdbapi.com/?s={query}&apikey=bb1856c2')
            if response.status_code == 200:
                data = response.json()
                movies = data.get('Search', [])
                # Fetch recommendations based on the first movie's genre
                if movies:
                    first_movie_id = movies[0].get('imdbID')
                    genre_response = requests.get(f'http://www.omdbapi.com/?i={first_movie_id}&apikey=bb1856c2')
                    if genre_response.status_code == 200:
                        genre_data = genre_response.json()
                        first_movie_genre = genre_data.get('Genre', '').split(',')[0].strip()
                        rec_response = requests.get(f'http://www.omdbapi.com/?s={first_movie_genre}&apikey=bb1856c2')
                        if rec_response.status_code == 200:
                            rec_data = rec_response.json()
                            recommendations = rec_data.get('Search', [])
        return render_template('search.html', movies=movies, query=query, recommendations=recommendations)
    return redirect(url_for('login'))

# Movie Details Route
@app.route('/movie/<imdb_id>')
def movie(imdb_id):
    if is_logged_in():
        response = requests.get(f'http://www.omdbapi.com/?i={imdb_id}&apikey=bb1856c2')
        if response.status_code == 200:
            movie_details = response.json()
            # Fetch similar movies based on the current movie's genre
            if movie_details and movie_details.get('Response') == 'True':
                genres = movie_details.get('Genre', '').split(',')
                recommendations = []
                for genre in genres:
                    genre = genre.strip()
                    rec_response = requests.get(f'http://www.omdbapi.com/?s={genre}&apikey=bb1856c2')
                    if rec_response.status_code == 200:
                        rec_data = rec_response.json()
                        if rec_data.get('Search'):
                            recommendations.extend(rec_data['Search'])
                # Remove duplicates
                recommendations = list({v['imdbID']: v for v in recommendations}.values())
                # Fetch actor images
                actor_images = get_actor_images(movie_details.get('Actors', ''))
            else:
                recommendations = []
                actor_images = {}
            return render_template('movie_details.html', movie=movie_details, recommendations=recommendations, actor_images=actor_images)
        else:
            return render_template('movie_details.html', movie={})  # Handle if movie not found
    return redirect(url_for('login'))

# Video Play Route
@app.route('/play/<imdb_id>')
def play(imdb_id):
    if is_logged_in():
        return render_template('play.html', imdb_id=imdb_id)
    return redirect(url_for('login'))

# Search Recommendations Route
@app.route('/search_recommendations', methods=['GET'])
def search_recommendations():
    query = request.args.get('query')
    if query:
        response = requests.get(f'http://www.omdbapi.com/?s={query}&apikey=bb1856c2')
        if response.status_code == 200:
            data = response.json()
            return jsonify(data.get('Search', []))
    return jsonify([])

# User Profile Route
@app.route('/profile')
def profile():
    if is_logged_in():
        username = session['username']
        user_watchlist = watchlist.get(username, [])
        return render_template('profile.html', username=username, watchlist=user_watchlist)
    return redirect(url_for('login'))

# Add to Watchlist Route
@app.route('/add_to_watchlist/<imdb_id>')
def add_to_watchlist(imdb_id):
    if is_logged_in():
        username = session['username']
        if username not in watchlist:
            watchlist[username] = []
        if imdb_id not in watchlist[username]:
            watchlist[username].append(imdb_id)
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

# Remove from Watchlist Route
@app.route('/remove_from_watchlist/<imdb_id>')
def remove_from_watchlist(imdb_id):
    if is_logged_in():
        username = session['username']
        if username in watchlist and imdb_id in watchlist[username]:
            watchlist[username].remove(imdb_id)
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

# Secret Route for 18+ Adult Movies
@app.route('/adult_movies')
def adult_movies():
    if is_logged_in():
        # Example IDs for adult movies
        adult_ids = ['tt0118689', 'tt0118691', 'tt0118694']  # Random adult movie IDs
        adult_movies = []
        for imdb_id in adult_ids:
            response = requests.get(f'http://www.omdbapi.com/?i={imdb_id}&apikey=bb1856c2')
            if response.status_code == 200:
                movie_data = response.json()
                if movie_data and movie_data.get('Response') == 'True':
                    adult_movies.append(movie_data)
        return render_template('adult_movies.html', adult_movies=adult_movies)
    return redirect(url_for('login'))

# Running the Flask app
if __name__ == '__main__':
    app.run(debug=True)