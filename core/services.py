import requests
import os

# API KEY
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_URL = "https://api.themoviedb.org/3"
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"

def search_content_service(query):
    """
    Hem film hem kitap arar.
    """
    movies = search_movies(query)
    books = search_books(query)
    return {'movies': movies, 'books': books}

def search_movies(query):
    """
    TMDb Film Arama
    """
    if not query: return []
    url = f"{TMDB_URL}/search/movie"
    params = {'api_key': TMDB_API_KEY, 'query': query, 'language': 'tr-TR'}
    try:
        response = requests.get(url, params=params)
        return response.json().get('results', []) if response.status_code == 200 else []
    except: return []

def search_books(query):
    """
    Google Books Kitap Arama (Temizlenmiş Veri)
    """
    if not query: return []
    params = {'q': query, 'maxResults': 10}
    
    try:
        response = requests.get(GOOGLE_BOOKS_URL, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            cleaned_books = []
            
            for item in items:
                info = item.get('volumeInfo', {})
                
                # Kapak resmi kontrolü
                image_links = info.get('imageLinks', {})
                cover = image_links.get('thumbnail') or image_links.get('smallThumbnail')
                
                # Yazar listesini metne çevir
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
    """
    Film Detayı Çekme
    """
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
    """
    Kitap Detayı Çekme (BU EKSİKTİ!)
    """
    url = f"{GOOGLE_BOOKS_URL}/{google_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Kitap Hatası: {e}")
    return None