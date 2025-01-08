from flask import Flask, render_template, request, jsonify
import pandas as pd
from joblib import load
import requests
from functools import lru_cache

# Tạo ứng dụng Flask
app = Flask(__name__)

# Load mô hình và dữ liệu
model_path = 'models/SVD++_model_item_based_best.joblib'
trained_model = load(model_path)

ratings_path = 'data/data_cleaned.csv'
ratings_data = pd.read_csv(ratings_path)

links_path = 'data/links.csv'
links_data = pd.read_csv(links_path)

# Lấy danh sách user_id và movie_titles
user_ids = ratings_data['userId'].unique().tolist()
movie_titles = ratings_data[['movieId', 'title']].drop_duplicates().sort_values('title')

# Chuyển đổi links_data thành dictionary để truy cập nhanh
links_dict = links_data.set_index('movieId').to_dict('index')

# Caching TMDB API để lấy thông tin phim
@lru_cache(maxsize=500)
def get_tmdb_details_cached(tmdb_id):
    """Lấy thông tin mô tả và hình ảnh từ TMDB API với caching."""
    tmdb_api_key = 'eb5621ed52a0ec964b95819efc7a8a90'  # TMDB API Key
    tmdb_url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}?api_key={tmdb_api_key}"
    try:
        response = requests.get(tmdb_url)
        if response.status_code == 200:
            data = response.json()
            poster_path = data.get('poster_path')
            overview = data.get('overview', 'No description available.')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            return overview, poster_url
    except Exception as e:
        print(f"Lỗi lấy TMDB Details: {e}")
    return None, None

# Route chính
@app.route('/')
def index():
    return render_template('index.html', user_ids=user_ids, movie_titles=movie_titles)

# Route xử lý gợi ý phim
@app.route('/recommend', methods=['POST'])
def recommend():
    user_id = int(request.form['user_id'])
    movie_title = request.form['movie_title']

    # Lấy movie_id từ title
    movie_id_row = movie_titles[movie_titles['title'] == movie_title]
    if movie_id_row.empty:
        return jsonify({"error": "Movie title not found in dataset."})
    movie_id = movie_id_row['movieId'].values[0]

    # Dự đoán và gợi ý phim
    all_movie_ids = ratings_data['movieId'].unique()
    watched_movie_ids = ratings_data[ratings_data['userId'] == user_id]['movieId'].unique()
    candidate_movie_ids = [mid for mid in all_movie_ids if mid not in watched_movie_ids]

    recommendations = []
    for candidate_movie_id in candidate_movie_ids:
        prediction = trained_model.predict(user_id, candidate_movie_id)
        recommendations.append((candidate_movie_id, prediction.est))

    # Sắp xếp theo điểm dự đoán giảm dần
    recommendations = sorted(recommendations, key=lambda x: x[1], reverse=True)[:12]

    # Chuẩn bị thông tin chi tiết cho các phim được gợi ý
    detailed_recommendations = []
    for movie_id, predicted_rating in recommendations:
        if movie_id not in links_dict:
            continue  # Bỏ qua nếu không có thông tin links
        
        imdb_id = links_dict[movie_id].get('imdbId')
        tmdb_id = links_dict[movie_id].get('tmdbId')
        description, poster_url = get_tmdb_details_cached(tmdb_id)

        detailed_recommendations.append({
            'title': movie_titles[movie_titles['movieId'] == movie_id]['title'].values[0],
            'predicted_rating': f"{predicted_rating:.2f}",
            'imdb_link': f"https://www.imdb.com/title/tt{int(imdb_id):07d}" if imdb_id else "N/A",
            'tmdb_link': f"https://www.themoviedb.org/movie/{int(tmdb_id)}" if tmdb_id else "N/A",
            'poster_url': poster_url,
            'description': description
        })

    return jsonify(detailed_recommendations)

if __name__ == '__main__':
    app.run(debug=True)
