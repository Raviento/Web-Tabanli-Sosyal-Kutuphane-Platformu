from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Movie, Book, Activity, UserList, Profile
from .serializers import MovieSerializer, BookSerializer, ActivitySerializer
from .services import search_content_service, get_movie_detail_service, get_book_detail_service
from .forms import ProfileUpdateForm

# --- API VIEWSETS ---
class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class FeedViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Activity.objects.all().order_by('-created_at')

class SearchView(APIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Arama terimi (q) gerekli."}, status=400)
        results = search_content_service(query)
        return Response(results)

# --- FRONTEND VIEWS ---
def index(request):
    return render(request, 'index.html')

def movie_detail(request, tmdb_id):
    movie_data = get_movie_detail_service(tmdb_id)
    if not movie_data: return render(request, '404.html')
    return render(request, 'movie_detail.html', {'movie': movie_data})

def book_detail(request, google_id):
    book_data = get_book_detail_service(google_id)
    if not book_data:
        return render(request, '404.html')
    
    info = book_data.get('volumeInfo', {})
    images = info.get('imageLinks', {})
    
    # Resim linkini al ve iyileştir
    cover = images.get('extraLarge') or images.get('large') or images.get('medium') or images.get('thumbnail')
    
    # Google bazen http verir, tarayıcılar bunu engeller. https yapalım.
    if cover:
        cover = cover.replace('http://', 'https://')

    context = {
        'book': {
            'id': book_data.get('id'),
            'title': info.get('title'),
            'authors': info.get('authors', ['Yazar Bilinmiyor']),
            'description': info.get('description', 'Özet yok.'),
            'page_count': info.get('pageCount'),
            'categories': info.get('categories', []),
            'published_date': info.get('publishedDate'),
            'publisher': info.get('publisher'),
            'cover_url': cover, # Güncellenmiş link
            'language': info.get('language'),
            'preview_link': info.get('previewLink')
        }
    }
    return render(request, 'book_detail.html', context)

# --- INTERACTION API (HEM FILM HEM KITAP) ---
class MovieInteractionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        action = data.get('action')
        list_type = data.get('list_type')
        
        movie_data = data.get('movie_data')
        book_data = data.get('book_data')
        target_object = None

        # FİLM KAYDETME
        if movie_data:
            movie, created = Movie.objects.get_or_create(
                tmdb_id=movie_data['id'],
                defaults={
                    'title': movie_data['title'],
                    'poster_path': movie_data.get('poster_path', ''),
                    'release_date': movie_data.get('release_date') or None,
                    'overview': movie_data.get('overview', ''),
                    'vote_average': float(str(movie_data.get('vote_average', 0)).replace(',', '.'))
                }
            )
            target_object = movie

        # KİTAP KAYDETME
        elif book_data:
            # Yazarları string olarak kaydetmek için listeyi birleştiriyoruz
            authors_str = ", ".join(book_data.get('authors', [])) if isinstance(book_data.get('authors'), list) else book_data.get('authors', '')
            
            book, created = Book.objects.get_or_create(
                google_id=book_data['google_id'],
                defaults={
                    'title': book_data['title'],
                    'authors': authors_str,
                    'description': book_data.get('description', ''),
                    'cover_path': book_data.get('cover_path', ''),
                    'page_count': int(book_data.get('page_count') or 0)
                }
            )
            target_object = book
        else:
            return Response({'error': 'Veri eksik'}, status=400)

        # LİSTEYE EKLEME
        if action == 'add_to_list':
            user_list, _ = UserList.objects.get_or_create(user=user, list_type=list_type, defaults={'name': list_type})
            
            if isinstance(target_object, Movie):
                if target_object not in user_list.movies.all():
                    user_list.movies.add(target_object)
                    Activity.objects.create(user=user, action_type='ADDED_LIST', movie=target_object, related_list=user_list)
                    return Response({'status': 'added', 'message': 'Film eklendi!'})
            
            elif isinstance(target_object, Book):
                if target_object not in user_list.books.all():
                    user_list.books.add(target_object)
                    Activity.objects.create(user=user, action_type='ADDED_LIST', book=target_object, related_list=user_list)
                    return Response({'status': 'added', 'message': 'Kitap eklendi!'})

            return Response({'status': 'exists', 'message': 'Zaten ekli.'})

        return Response({'error': 'İşlem geçersiz'}, status=400)

# --- AUTH & PROFILE ---
def register_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Kullanıcı adı dolu.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('home')
    return render(request, 'register.html')

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile, created = Profile.objects.get_or_create(user=user)
    
    watched_list = UserList.objects.filter(user=user, list_type='watched').first()
    watchlist = UserList.objects.filter(user=user, list_type='watchlist').first()
    
    # Kitap listelerini de çekelim (PDF Madde 80)
    read_list = UserList.objects.filter(user=user, list_type='read').first()
    readlist = UserList.objects.filter(user=user, list_type='readlist').first()

    context = {
        'profile_user': user,
        'profile': profile,
        'watched_movies': watched_list.movies.all() if watched_list else [],
        'watchlist_movies': watchlist.movies.all() if watchlist else [],
        'read_books': read_list.books.all() if read_list else [],
        'readlist_books': readlist.books.all() if readlist else [],
        'is_owner': request.user == user
    }
    return render(request, 'profile.html', context)

@login_required
def edit_profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile', username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})