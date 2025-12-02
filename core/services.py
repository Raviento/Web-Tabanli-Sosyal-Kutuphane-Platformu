import requests
import os
from django.contrib.auth.models import User
from concurrent.futures import ThreadPoolExecutor, as_completed

# API KEY (TMDb için gerekli, Google Books için gerekmez)
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_URL = "https://api.themoviedb.org/3"
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"

def get_movie_director(movie_id):
    url = f"{TMDB_URL}/movie/{movie_id}/credits"
    params = {'api_key': TMDB_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=2)
        if response.status_code == 200:
            crew = response.json().get('crew', [])
            directors = [member['name'] for member in crew if member['job'] == 'Director']
            return ", ".join(directors)
    except:
        pass
    return ""

def search_content_service(query):
    """
    Hem film, hem kitap, hem de kullanıcı arar ve sonuçları birleştirip döner.
    """
    movies = search_movies(query)
    books = search_books(query)
    
    # Kullanıcı Arama
    users = User.objects.filter(username__icontains=query, is_superuser=False)[:5]
    user_results = []
    for user in users:
        avatar_url = user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else None
        user_results.append({
            'username': user.username,
            'avatar': avatar_url
        })

    return {'movies': movies, 'books': books, 'users': user_results}

def search_movies(query):
    if not query: return []
    url = f"{TMDB_URL}/search/movie"
    params = {'api_key': TMDB_API_KEY, 'query': query, 'language': 'tr-TR'}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get('results', [])
            
            # İlk 10 sonuç için yönetmen bilgisini paralel çek
            # Hepsini çekersek çok yavaşlar
            top_results = results[:10]
            remaining_results = results[10:]
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_movie = {executor.submit(get_movie_director, movie['id']): movie for movie in top_results}
                
                for future in as_completed(future_to_movie):
                    movie = future_to_movie[future]
                    try:
                        movie['director'] = future.result()
                    except:
                        movie['director'] = ""
            
            return top_results + remaining_results
        return []
    except: return []

def search_books(query):
    """
    Google Books Arama - HTTP linklerini HTTPS'e çevirir.
    """
    if not query: return []
    # Dil kısıtlaması yok, her dilden kitap gelir. maxResults artırıldı.
    params = {'q': query, 'maxResults': 40}
    
    try:
        response = requests.get(GOOGLE_BOOKS_URL, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            cleaned_books = []
            
            for item in items:
                info = item.get('volumeInfo', {})
                image_links = info.get('imageLinks', {})
                
                # Resim linkini al
                # API'den gelen linkler bazen bozuk veya "publisher/content" olduğu için erişilemez olabiliyor.
                # Bu yüzden standart Google Books görsel linkini kendimiz oluşturuyoruz.
                google_id = item.get('id')
                # Arama sonuçlarında da net gözükmesi için h=500 yeterli
                cover = f"https://books.google.com/books/content?id={google_id}&printsec=frontcover&img=1&zoom=1&h=500&source=gbs_api"

                # Yazarları string yap
                authors = ", ".join(info.get('authors', [])) if info.get('authors') else "Yazar Bilinmiyor"

                cleaned_books.append({
                    'google_id': item.get('id'),
                    'title': info.get('title', 'Başlıksız'),
                    'authors': authors,
                    'cover_url': cover
                })
            
            return cleaned_books
            
    except Exception as e:
        print(f"Google Books Hatası: {e}")
        return []
    
    return []

def get_movie_detail_service(tmdb_id):
    url = f"{TMDB_URL}/movie/{tmdb_id}"
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'tr-TR',
        'append_to_response': 'credits'
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Hata: {e}")
    return None

def get_book_detail_service(google_id):
    url = f"{GOOGLE_BOOKS_URL}/{google_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Kitap Hatası: {e}")
    return None

# --- YENİ EKLENEN SERVİSLER ---

def _fetch_tmdb_movies(url, params):
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            results = response.json().get('results', [])
            for m in results:
                if m.get('poster_path'):
                    m['image'] = f"https://image.tmdb.org/t/p/w500{m['poster_path']}"
                m['subtitle'] = m.get('release_date', '')[:4] if m.get('release_date') else ''
            return results
    except Exception as e:
        print(f"TMDB Error: {e}")
    return []

def get_popular_movies():
    url = f"{TMDB_URL}/movie/popular"
    params = {'api_key': TMDB_API_KEY, 'language': 'tr-TR', 'page': 1}
    return _fetch_tmdb_movies(url, params)

def get_top_rated_movies():
    url = f"{TMDB_URL}/movie/top_rated"
    params = {'api_key': TMDB_API_KEY, 'language': 'tr-TR', 'page': 1}
    return _fetch_tmdb_movies(url, params)

def get_movie_genres():
    url = f"{TMDB_URL}/genre/movie/list"
    params = {'api_key': TMDB_API_KEY, 'language': 'tr-TR'}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('genres', [])
    except:
        pass
    return []

def get_movies_by_genre(genre_id):
    url = f"{TMDB_URL}/discover/movie"
    params = {
        'api_key': TMDB_API_KEY, 
        'language': 'tr-TR', 
        'with_genres': genre_id,
        'sort_by': 'popularity.desc'
    }
    return _fetch_tmdb_movies(url, params)

def discover_movies(genre_id=None, year=None, min_score=None):
    url = f"{TMDB_URL}/discover/movie"
    params = {
        'api_key': TMDB_API_KEY, 
        'language': 'tr-TR', 
        'sort_by': 'popularity.desc',
        'vote_count.gte': 100  # Anlamsız sonuçları elemek için
    }
    
    if genre_id:
        params['with_genres'] = genre_id
    if year:
        params['primary_release_year'] = year
    if min_score:
        params['vote_average.gte'] = min_score
        
    return _fetch_tmdb_movies(url, params)

def get_books_by_category(query):
    # Google Books'ta kategori araması "subject:kategori" şeklinde yapılır
    # Ancak view tarafında zaten tam sorgu gönderiliyor, o yüzden direkt arama yapıyoruz.
    if query.startswith('subject:'):
        return search_books(query)
    return search_books(f"subject:{query}")