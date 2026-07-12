from flask import Flask, render_template, request, redirect, url_for

import pickle
import requests

app = Flask(
    __name__,
)

movies = pickle.load(open('movies.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

with open("tmdb_api_key.txt", "r") as f:
    TMDB_API_KEY = f.read().strip()


def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    data = requests.get(url).json()
    poster_path = data.get('poster_path')
    rating = data.get('vote_average')
    overview = data.get('overview')

    full_path = "https://image.tmdb.org/t/p/w500" + poster_path if poster_path else ""
    return full_path, rating, overview


def recommend(movie):
    movie = movie.lower()
    if movie not in movies['title'].str.lower().values:
        return [], [], [], []

    index = movies[movies['title'].str.lower() == movie].index[0]
    distances = similarity[index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies, posters, ratings, description = [], [], [], []

    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        poster, rating, overview = fetch_poster(movie_id)

        recommended_movies.append(movies.iloc[i[0]].title)
        posters.append(poster)
        ratings.append(rating)
        description.append(overview)

    return recommended_movies, posters, ratings, description

@app.route('/')
def home():
    movie_list = movies['title'].values
    return render_template("index.html", movie_list=movie_list)

@app.route('/recommend', methods=['POST'])
def recommend_movie():
    movie_name = request.form['movie']
    names, posters, ratings, desc = recommend(movie_name)

    # temporary global/session store 
    app.config['RESULT'] = {
        "movie": movie_name,
        "data": list(zip(names, posters, ratings, desc))
    }

    return redirect(url_for('result'))


@app.route('/result')
def result():
    movie_list = movies['title'].values
    result = app.config.pop('RESULT', None)

    if result:
        return render_template(
            "index.html",
            movie_list=movie_list,
            recommendations=result["data"],
            selected_movie=result["movie"]
        )

    # refresh or direct access clear UI
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
