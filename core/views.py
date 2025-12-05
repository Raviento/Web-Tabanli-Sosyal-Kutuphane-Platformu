from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Movie, Book, Activity, UserList, Profile, Rating, Review, ActivityLike, ActivityComment, TVSeries
from .serializers import MovieSerializer, BookSerializer, ActivitySerializer
from .services import (
    search_content_service, get_movie_detail_service, get_book_detail_service,
    get_popular_movies, get_top_rated_movies, get_movie_genres, get_movies_by_genre,
    get_books_by_category, discover_movies,
    get_popular_tv_series, get_top_rated_tv_series, get_tv_series_detail_service,
    get_tv_genres, get_tv_series_by_genre
)
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
        
        raw_results = search_content_service(query)
        formatted_results = []

        # Filmleri formatla
        for movie in raw_results.get('movies', []):
            if not movie.get('title'): continue
            
            year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
            director = movie.get('director', '')
            subtitle = f"{year} | {director}" if director else year
            
            formatted_results.append({
                'type': 'movie',
                'id': movie.get('id'),
                'title': movie.get('title'),
                'image': f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get('poster_path') else None,
                'poster_path': movie.get('poster_path'),
                'subtitle': subtitle,
                'original_release_date': movie.get('release_date')
            })

        # Dizileri formatla
        for tv in raw_results.get('tv_series', []):
            if not tv.get('name'): continue # TV dizilerinde title yerine name kullanılır
            
            year = tv.get('first_air_date', '')[:4] if tv.get('first_air_date') else ''
            
            formatted_results.append({
                'type': 'tv',
                'id': tv.get('id'),
                'title': tv.get('name'),
                'image': f"https://image.tmdb.org/t/p/w500{tv.get('poster_path')}" if tv.get('poster_path') else None,
                'poster_path': tv.get('poster_path'),
                'subtitle': f"Dizi | {year}",
                'original_release_date': tv.get('first_air_date')
            })

        # Kitapları formatla
        for book in raw_results.get('books', []):
            if not book.get('title'): continue
            
            formatted_results.append({
                'type': 'book',
                'id': book.get('google_id'),
                'title': book.get('title'),
                'image': book.get('cover_url'),
                'subtitle': book.get('authors')
            })

        # Kullanıcıları formatla (Opsiyonel, şu an listeye eklemede kullanılmıyor ama aramada çıkabilir)
        for user in raw_results.get('users', []):
            formatted_results.append({
                'type': 'user',
                'username': user['username'], # Frontend bu alanı bekliyor
                'title': user['username'],
                'image': user['avatar'] or '/media/avatars/usericon.png',
                'avatar': user['avatar'], # Frontend bu alanı bekliyor
                'subtitle': 'Kullanıcı'
            })

        # Frontend (index.html) ayrı ayrı array'ler bekliyor olabilir.
        # Hem 'results' (tek liste) hem de ayrı ayrı listeler dönelim.
        
        response_data = {
            'results': formatted_results,
            'movies': [r for r in formatted_results if r['type'] == 'movie'],
            'tv_series': [r for r in formatted_results if r['type'] == 'tv'],
            'books': [r for r in formatted_results if r['type'] == 'book'],
            'users': [r for r in formatted_results if r['type'] == 'user']
        }

        return Response(response_data)

from django.core.paginator import Paginator

def get_platform_popular_movies():
    # Platformda en çok etkileşim alan filmler
    popular_movies = Movie.objects.annotate(
        interaction_count=Count('activity')
    ).order_by('-interaction_count')[:6]
    
    results = []
    for movie in popular_movies:
        results.append({
            'id': movie.tmdb_id,
            'title': movie.title,
            'image': f"https://image.tmdb.org/t/p/w500{movie.poster_path}" if movie.poster_path else None,
            'subtitle': f"{movie.interaction_count} Etkileşim",
            'vote_average': movie.vote_average
        })
    return results

def get_platform_top_rated_movies():
    # Platformda en yüksek puanlı filmler
    top_rated = Rating.objects.filter(movie__isnull=False).values('movie').annotate(
        avg_score=Avg('score'),
        count=Count('id')
    ).filter(count__gte=1).order_by('-avg_score')[:6]
    
    results = []
    for item in top_rated:
        try:
            movie = Movie.objects.get(id=item['movie'])
            results.append({
                'id': movie.tmdb_id,
                'title': movie.title,
                'image': f"https://image.tmdb.org/t/p/w500{movie.poster_path}" if movie.poster_path else None,
                'subtitle': f"{item['avg_score']:.1f} Puan",
                'vote_average': item['avg_score']
            })
        except Movie.DoesNotExist:
            continue
    return results

def get_platform_popular_books():
    # Platformda en çok etkileşim alan kitaplar
    popular_books = Book.objects.annotate(
        interaction_count=Count('activity')
    ).order_by('-interaction_count')[:6]
    
    results = []
    for book in popular_books:
        results.append({
            'google_id': book.google_id,
            'title': book.title,
            'image': book.cover_path,
            'subtitle': f"{book.interaction_count} Etkileşim",
            'authors': book.authors
        })
    return results

# --- FRONTEND VIEWS ---
def explore(request):
    # Keşfet Sayfası: Takip edilen/edilmeyen herkesin aktiviteleri
    if request.user.is_authenticated:
        activity_list = Activity.objects.exclude(user=request.user).select_related('user', 'user__profile', 'movie', 'book').order_by('-created_at')
    else:
        activity_list = Activity.objects.select_related('user', 'user__profile', 'movie', 'book').all().order_by('-created_at')
    
    paginator = Paginator(activity_list, 10) 
    page_number = request.GET.get('page')
    activities = paginator.get_page(page_number)

    for activity in activities:
        activity.like_count = activity.likes.count()
        activity.comment_list = activity.comments.select_related('user', 'user__profile').order_by('created_at')
        if request.user.is_authenticated:
            activity.is_liked = activity.likes.filter(user=request.user).exists()
            
            target_id = activity.original_activity.id if activity.action_type == 'SHARED' else activity.id
            activity.is_shared = Activity.objects.filter(
                user=request.user, 
                action_type='SHARED', 
                original_activity_id=target_id
            ).exists()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = ""
        for activity in activities:
            html += render_to_string('partials/activity_card.html', {'activity': activity, 'user': request.user}, request=request)
        
        return JsonResponse({
            'html': html,
            'has_next': activities.has_next(),
            'next_page_number': activities.next_page_number() if activities.has_next() else None
        })
    
    # Vitrin Verileri
    platform_popular_movies = get_platform_popular_movies()
    platform_top_rated_movies = get_platform_top_rated_movies()
    platform_popular_books = get_platform_popular_books()
    
    api_popular_movies = get_popular_movies()[:6]
    api_top_rated_movies = get_top_rated_movies()[:6]
    api_popular_books = get_books_by_category("subject:fiction")[:6]
    
    genres = get_movie_genres()
            
    context = {
        'activities': activities, 
        'page_title': 'Keşfet',
        'platform_popular_movies': platform_popular_movies,
        'platform_top_rated_movies': platform_top_rated_movies,
        'platform_popular_books': platform_popular_books,
        'api_popular_movies': api_popular_movies,
        'api_top_rated_movies': api_top_rated_movies,
        'api_popular_books': api_popular_books,
        'genres': genres
    }
    return render(request, 'explore.html', context)

def filter_content(request):
    content_type = request.GET.get('type', 'movie')
    genre_id = request.GET.get('genre')
    year = request.GET.get('year')
    min_score = request.GET.get('score')
    
    results = []
    
    if content_type == 'movie':
        results = discover_movies(genre_id=genre_id, year=year, min_score=min_score)
    elif content_type == 'book':
        query = f"subject:{genre_id}" if genre_id else "subject:fiction"
        results = get_books_by_category(query)
        
    html = render_to_string('partials/filter_results.html', {'results': results, 'type': content_type})
    return JsonResponse({'html': html})

def index(request):
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        following_profiles = profile.following.all()
        following_users = [p.user for p in following_profiles]
        
        activity_list = Activity.objects.filter(user__in=following_users).select_related('user', 'user__profile', 'movie', 'book').order_by('-created_at')
    else:
        # Giriş yapmamışsa aktivite gösterme (Landing Page)
        activity_list = Activity.objects.none()
    
    paginator = Paginator(activity_list, 10) 
    page_number = request.GET.get('page')
    activities = paginator.get_page(page_number)

    for activity in activities:
        activity.like_count = activity.likes.count()
        activity.comment_list = activity.comments.select_related('user', 'user__profile').order_by('created_at')
        if request.user.is_authenticated:
            activity.is_liked = activity.likes.filter(user=request.user).exists()
            
            target_id = activity.original_activity.id if activity.action_type == 'SHARED' else activity.id
            activity.is_shared = Activity.objects.filter(
                user=request.user, 
                action_type='SHARED', 
                original_activity_id=target_id
            ).exists()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = ""
        for activity in activities:
            html += render_to_string('partials/activity_card.html', {'activity': activity, 'user': request.user}, request=request)
        
        return JsonResponse({
            'html': html,
            'has_next': activities.has_next(),
            'next_page_number': activities.next_page_number() if activities.has_next() else None
        })
        
    return render(request, 'index.html', {'activities': activities, 'page_title': 'Zaman Tüneli'})

def movie_detail(request, tmdb_id):
    movie_data = get_movie_detail_service(tmdb_id)
    if not movie_data: return render(request, '404.html')
    
    context = {'movie': movie_data}
    
    # Platform İstatistikleri ve Yorumlar
    try:
        local_movie = Movie.objects.get(tmdb_id=tmdb_id)
        platform_stats = Rating.objects.filter(movie=local_movie).aggregate(avg_score=Avg('score'), total_votes=Count('id'))
        reviews = Review.objects.filter(movie=local_movie).select_related('user', 'user__profile').order_by('-created_at')
        
        if request.user.is_authenticated:
            user_rating = Rating.objects.filter(user=request.user, movie=local_movie).first()
            context['user_rating'] = user_rating
    except Movie.DoesNotExist:
        platform_stats = {'avg_score': None, 'total_votes': 0}
        reviews = []
        
    context['platform_stats'] = platform_stats
    context['reviews'] = reviews
    
    if request.user.is_authenticated:
        user_lists = UserList.objects.filter(user=request.user)
        try:
            movie_obj = Movie.objects.get(tmdb_id=tmdb_id)
            lists_containing_movie = user_lists.filter(movies=movie_obj).values_list('id', flat=True)
            standard_lists_containing = user_lists.filter(movies=movie_obj).exclude(list_type='custom').values_list('list_type', flat=True)
        except Movie.DoesNotExist:
            lists_containing_movie = []
            standard_lists_containing = []
            
        context['user_lists'] = user_lists
        context['lists_containing_movie'] = list(lists_containing_movie)
        context['standard_lists_containing'] = list(standard_lists_containing)

    return render(request, 'movie_detail.html', context)

def book_detail(request, google_id):
    book_data = get_book_detail_service(google_id)
    if not book_data: return render(request, '404.html')
    
    info = book_data.get('volumeInfo', {})
    
    # Resim linkini oluştur
    cover = f"https://books.google.com/books/content?id={book_data.get('id')}&printsec=frontcover&img=1&zoom=1&h=1000&source=gbs_api"

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
            'cover_url': cover,
            'language': info.get('language'),
            'preview_link': info.get('previewLink')
        }
    }

    # Platform İstatistikleri ve Yorumlar
    try:
        local_book = Book.objects.get(google_id=google_id)
        platform_stats = Rating.objects.filter(book=local_book).aggregate(avg_score=Avg('score'), total_votes=Count('id'))
        reviews = Review.objects.filter(book=local_book).select_related('user', 'user__profile').order_by('-created_at')
        
        if request.user.is_authenticated:
            user_rating = Rating.objects.filter(user=request.user, book=local_book).first()
            context['user_rating'] = user_rating
    except Book.DoesNotExist:
        platform_stats = {'avg_score': None, 'total_votes': 0}
        reviews = []
        
    context['platform_stats'] = platform_stats
    context['reviews'] = reviews

    if request.user.is_authenticated:
        user_lists = UserList.objects.filter(user=request.user)
        try:
            book_obj = Book.objects.get(google_id=google_id)
            lists_containing_book = user_lists.filter(books=book_obj).values_list('id', flat=True)
            standard_lists_containing = user_lists.filter(books=book_obj).exclude(list_type='custom').values_list('list_type', flat=True)
        except Book.DoesNotExist:
            lists_containing_book = []
            standard_lists_containing = []
            
        context['user_lists'] = user_lists
        context['lists_containing_book'] = list(lists_containing_book)
        context['standard_lists_containing'] = list(standard_lists_containing)

    return render(request, 'book_detail.html', context)

@login_required
def add_rating(request):
    if request.method == 'POST':
        target_type = request.POST.get('target_type')
        target_id = request.POST.get('target_id') # API ID
        score = int(request.POST.get('score'))
        
        target_obj = None
        if target_type == 'movie':
            try:
                target_obj = Movie.objects.get(tmdb_id=target_id)
            except Movie.DoesNotExist:
                pass
                
        elif target_type == 'book':
            try:
                target_obj = Book.objects.get(google_id=target_id)
            except Book.DoesNotExist:
                pass
        
        if target_obj:
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                movie=target_obj if target_type == 'movie' else None,
                book=target_obj if target_type == 'book' else None,
                defaults={'score': score}
            )
            
            activity, activity_created = Activity.objects.update_or_create(
                user=request.user,
                action_type='RATED',
                movie=target_obj if target_type == 'movie' else None,
                book=target_obj if target_type == 'book' else None,
                defaults={'related_rating': rating}
            )
            
            if not activity_created:
                from django.utils import timezone
                activity.created_at = timezone.now()
                activity.save()
            
            messages.success(request, 'Puanınız kaydedildi.')
        else:
            messages.error(request, 'İçerik bulunamadı. Önce listeye eklemeyi deneyin.')
            
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def add_review(request):
    if request.method == 'POST':
        target_type = request.POST.get('target_type')
        target_id = request.POST.get('target_id')
        text = request.POST.get('text')
        
        target_obj = None
        if target_type == 'movie':
            target_obj = Movie.objects.filter(tmdb_id=target_id).first()
        elif target_type == 'book':
            target_obj = Book.objects.filter(google_id=target_id).first()
            
        if target_obj and text:
            review = Review.objects.create(
                user=request.user,
                movie=target_obj if target_type == 'movie' else None,
                book=target_obj if target_type == 'book' else None,
                text=text
            )
            
            Activity.objects.create(
                user=request.user, 
                action_type='REVIEWED', 
                movie=target_obj if target_type == 'movie' else None,
                book=target_obj if target_type == 'book' else None,
                related_review=review
            )
            messages.success(request, 'Yorumunuz paylaşıldı.')
        else:
            messages.error(request, 'Hata oluştu.')
            
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    messages.success(request, 'Yorum silindi.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            review.text = text
            review.save()
            messages.success(request, 'Yorum güncellendi.')
        else:
            messages.error(request, 'Yorum boş olamaz.')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

# --- INTERACTION API ---
class MovieInteractionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data
        action = data.get('action')
        list_type = data.get('list_type')
        target_type = data.get('target_type')
        
        movie_data = data.get('movie_data')
        book_data = data.get('book_data')
        target_object = None

        # 1. Silme işlemi için özel durum (DB ID ile)
        if action == 'remove_from_list' and data.get('target_id'):
            try:
                if target_type == 'movie':
                    target_object = Movie.objects.get(id=data.get('target_id'))
                elif target_type == 'book':
                    target_object = Book.objects.get(id=data.get('target_id'))
            except (Movie.DoesNotExist, Book.DoesNotExist, ValueError):
                pass

        # 2. Eğer hala yoksa, veriden oluştur veya bul
        if not target_object:
            if not movie_data and target_type == 'movie':
                movie_data = {
                    'id': data.get('target_id'), # API ID
                    'title': data.get('title'),
                    'poster_path': data.get('poster_path'),
                    'release_date': data.get('release_date'),
                    'overview': data.get('overview'),
                    'vote_average': data.get('vote_average')
                }
            
            if not book_data and target_type == 'book':
                book_data = {
                    'google_id': data.get('google_id') or data.get('target_id'),
                    'title': data.get('title'),
                    'authors': data.get('authors'),
                    'description': data.get('description'),
                    'cover_path': data.get('cover_path'),
                    'page_count': data.get('page_count')
                }

            # Film Kaydetme / Bulma
            if movie_data and movie_data.get('id'):
                try:
                    vote_avg = float(str(movie_data.get('vote_average', 0)).replace(',', '.'))
                except:
                    vote_avg = 0
                
                release_date = movie_data.get('release_date')
                if release_date:
                    if len(release_date) == 4: # Sadece yıl geldiyse
                        release_date = f"{release_date}-01-01"
                    elif len(release_date) != 10: # YYYY-MM-DD değilse
                        release_date = None
                else:
                    release_date = None

                movie, created = Movie.objects.get_or_create(
                    tmdb_id=movie_data['id'],
                    defaults={
                        'title': movie_data.get('title') or 'Bilinmiyor',
                        'poster_path': movie_data.get('poster_path') or '',
                        'release_date': release_date,
                        'overview': movie_data.get('overview') or '',
                        'vote_average': vote_avg
                    }
                )
                target_object = movie

            # Kitap Kaydetme / Bulma
            elif book_data and book_data.get('google_id'):
                authors_str = book_data.get('authors') or ''
                if isinstance(authors_str, list): authors_str = ", ".join(authors_str)
                
                google_id = book_data['google_id']
                # Resim linkini standart formata zorla (Eğer tam link gelmediyse)
                raw_cover = book_data.get('cover_path') or ''
                if raw_cover and 'http' not in raw_cover:
                     raw_cover = f"https://books.google.com/books/content?id={google_id}&printsec=frontcover&img=1&zoom=1&h=1000&source=gbs_api"

                try:
                    page_count = int(book_data.get('page_count') or 0)
                except:
                    page_count = 0

                book, created = Book.objects.get_or_create(
                    google_id=google_id,
                    defaults={
                        'title': book_data.get('title') or 'Bilinmiyor',
                        'authors': authors_str,
                        'description': book_data.get('description') or '',
                        'cover_path': raw_cover,
                        'page_count': page_count
                    }
                )
                target_object = book
        
        if not target_object:
            return Response({'error': 'Veri eksik veya içerik bulunamadı'}, status=400)

        # LİSTEYE EKLEME / ÇIKARMA
        if action in ['add_to_list', 'remove_from_list']:
            list_id = data.get('list_id')
            
            if list_id:
                # Özel liste veya ID ile belirtilen liste
                user_list = get_object_or_404(UserList, id=list_id, user=user)
            else:
                # Standart liste
                user_list, _ = UserList.objects.get_or_create(user=user, list_type=list_type, defaults={'name': list_type})
            
            if action == 'add_to_list':
                if isinstance(target_object, Movie):
                    if target_object not in user_list.movies.all():
                        user_list.movies.add(target_object)
                        Activity.objects.create(user=user, action_type='ADDED_LIST', movie=target_object, related_list=user_list)
                        return Response({'status': 'added', 'message': f'{user_list.name} listesine eklendi!'})
                elif isinstance(target_object, Book):
                    if target_object not in user_list.books.all():
                        user_list.books.add(target_object)
                        Activity.objects.create(user=user, action_type='ADDED_LIST', book=target_object, related_list=user_list)
                        return Response({'status': 'added', 'message': f'{user_list.name} listesine eklendi!'})
                return Response({'status': 'exists', 'message': 'Zaten ekli.'})
            
            elif action == 'remove_from_list':
                if isinstance(target_object, Movie):
                    user_list.movies.remove(target_object)
                elif isinstance(target_object, Book):
                    user_list.books.remove(target_object)
                return Response({'status': 'removed', 'message': f'{user_list.name} listesinden çıkarıldı.'})

        return Response({'error': 'İşlem geçersiz'}, status=400)

# --- AUTH & PROFILE ---
def register_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm:
            messages.error(request, "Şifreler eşleşmiyor.")
            return render(request, 'register.html')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Bu kullanıcı adı zaten kullanımda.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Bu e-posta zaten kullanımda.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('home')
    return render(request, 'register.html')

def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "E-posta veya şifre hatalı.")
        except User.DoesNotExist:
            messages.error(request, "E-posta veya şifre hatalı.")
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile, created = Profile.objects.get_or_create(user=user)
    
    watched_list = UserList.objects.filter(user=user, list_type='watched').first()
    watchlist = UserList.objects.filter(user=user, list_type='watchlist').first()
    read_list = UserList.objects.filter(user=user, list_type='read').first()
    readlist = UserList.objects.filter(user=user, list_type='readlist').first()
    
    custom_lists = UserList.objects.filter(user=user, list_type='custom')
    
    # Son Aktiviteler
    all_activities = Activity.objects.filter(user=user, action_type__in=['RATED', 'REVIEWED', 'ADDED_LIST', 'COMMENTED']).order_by('-created_at')
    recent_activities_data = []
    seen_items_for_non_reviews = set()
    
    for activity in all_activities:
        item_key = None
        if activity.movie:
            item_key = f"movie_{activity.movie.id}"
        elif activity.book:
            item_key = f"book_{activity.book.id}"
        else:
            continue
            
        if activity.action_type in ['REVIEWED', 'COMMENTED']:
            score = None
            if activity.related_rating:
                score = activity.related_rating.score
            else:
                if activity.movie:
                    r = Rating.objects.filter(user=user, movie=activity.movie).first()
                    if r: score = r.score
                elif activity.book:
                    r = Rating.objects.filter(user=user, book=activity.book).first()
                    if r: score = r.score
            
            recent_activities_data.append({
                'activity': activity,
                'score': score
            })
            seen_items_for_non_reviews.add(item_key)

        elif item_key not in seen_items_for_non_reviews:
            score = None
            if activity.action_type == 'RATED' and activity.related_rating:
                score = activity.related_rating.score
            else:
                if activity.movie:
                    r = Rating.objects.filter(user=user, movie=activity.movie).first()
                    if r: score = r.score
                elif activity.book:
                    r = Rating.objects.filter(user=user, book=activity.book).first()
                    if r: score = r.score

            recent_activities_data.append({
                'activity': activity,
                'score': score
            })
            seen_items_for_non_reviews.add(item_key)
        
        if len(recent_activities_data) >= 10:
            break

    stats = {
        'films_count': Activity.objects.filter(user=user, movie__isnull=False).count(),
        'books_count': Activity.objects.filter(user=user, book__isnull=False).count(),
        'lists_count': UserList.objects.filter(user=user).count(),
        'reviews_count': Activity.objects.filter(user=user, action_type='REVIEWED').count(),
    }

    # Favori Filmler
    all_rated_movies = Activity.objects.filter(user=user, movie__isnull=False, action_type='RATED') \
        .order_by('-related_rating__score', '-created_at')
    
    favorite_films = []
    seen_movies = set()
    
    for activity in all_rated_movies:
        if activity.movie.id not in seen_movies:
            favorite_films.append(activity)
            seen_movies.add(activity.movie.id)
        
        if len(favorite_films) >= 4:
            break

    is_following = False
    if request.user.is_authenticated and request.user != user:
        current_user_profile, _ = Profile.objects.get_or_create(user=request.user)
        is_following = current_user_profile.following.filter(id=profile.id).exists()

    context = {
        'profile_user': user,
        'profile': profile,
        'stats': stats,
        'favorite_films': favorite_films,
        'followers': profile.followers.all(),
        'following': profile.following.all(),
        'followers_count': profile.followers.count(),
        'following_count': profile.following.count(),
        'watched_movies': watched_list.movies.all() if watched_list else [],
        'watchlist_movies': watchlist.movies.all() if watchlist else [],
        'read_books': read_list.books.all() if read_list else [],
        'readlist_books': readlist.books.all() if readlist else [],
        'custom_lists': custom_lists,
        'recent_activities': recent_activities_data,
        'is_owner': request.user == user,
        'is_following': is_following
    }
    return render(request, 'profile.html', context)

@login_required
def follow_user(request, username):
    target_user = get_object_or_404(User, username=username)
    if target_user == request.user:
        return redirect('profile', username=username)
        
    user_profile, _ = Profile.objects.get_or_create(user=request.user)
    target_profile, _ = Profile.objects.get_or_create(user=target_user)
    
    if user_profile.following.filter(id=target_profile.id).exists():
        user_profile.following.remove(target_profile)
    else:
        user_profile.following.add(target_profile)
        
    return redirect('profile', username=username)

@login_required
def remove_follower(request, username):
    # username: Beni takip eden ve çıkarmak istediğim kullanıcı
    follower_user = get_object_or_404(User, username=username)
    
    my_profile, _ = Profile.objects.get_or_create(user=request.user)
    follower_profile, _ = Profile.objects.get_or_create(user=follower_user)
    
    # Onların takip ettikleri listesinden beni çıkar
    if follower_profile.following.filter(id=my_profile.id).exists():
        follower_profile.following.remove(my_profile)
        
    return redirect('profile', username=request.user.username)

@login_required
def edit_profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Kullanıcı adını güncelle
            new_username = form.cleaned_data.get('username')
            if new_username and new_username != request.user.username:
                request.user.username = new_username
                request.user.save()
            
            form.save()
            messages.success(request, 'Profiliniz güncellendi.')
            return redirect('profile', username=request.user.username)
    else:
        # Formu açarken mevcut kullanıcı adını doldur
        form = ProfileUpdateForm(instance=profile, initial={'username': request.user.username})
    return render(request, 'edit_profile.html', {'form': form})

@login_required
def create_custom_list(request):
    if request.method == 'POST':
        list_name = request.POST.get('list_name')
        if list_name:
            UserList.objects.create(user=request.user, name=list_name, list_type='custom')
            messages.success(request, f"'{list_name}' listesi oluşturuldu.")
        else:
            messages.error(request, "Liste adı boş olamaz.")
    return redirect('profile', username=request.user.username)

def list_detail(request, list_id):
    user_list = get_object_or_404(UserList, id=list_id)
    is_owner = request.user == user_list.user
    
    context = {
        'user_list': user_list,
        'is_owner': is_owner,
        'movies': user_list.movies.all(),
        'books': user_list.books.all()
    }
    return render(request, 'list_detail.html', context)

@login_required
def like_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    like, created = ActivityLike.objects.get_or_create(user=request.user, activity=activity)
    
    if not created:
        # Zaten beğenmişse beğeniyi kaldır
        like.delete()
        liked = False
    else:
        liked = True
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'liked' if liked else 'unliked', 'like_count': activity.likes.count()})
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def add_activity_comment(request, activity_id):
    if request.method == 'POST':
        activity = get_object_or_404(Activity, id=activity_id)
        text = request.POST.get('text')
        if text:
            comment = ActivityComment.objects.create(user=request.user, activity=activity, text=text)
            
            # Yorum yapıldığında bunu da bir aktivite olarak kaydet
            Activity.objects.create(
                user=request.user,
                action_type='COMMENTED',
                original_activity=activity,
                related_comment=comment,
                movie=activity.movie,
                book=activity.book
            )
            
            messages.success(request, 'Yorumunuz eklendi.')
        else:
            messages.error(request, 'Yorum boş olamaz.')
            
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def share_activity(request, activity_id):
    original_activity = get_object_or_404(Activity, id=activity_id)
    
    # Eğer paylaşılan bir aktivite tekrar paylaşılıyorsa, orijinal kaynağı al
    target_activity = original_activity.original_activity if original_activity.action_type == 'SHARED' else original_activity
    
    # Paylaşım kontrolü (Toggle mantığı)
    existing_share = Activity.objects.filter(
        user=request.user,
        action_type='SHARED',
        original_activity=target_activity
    ).first()

    if existing_share:
        existing_share.delete()
        messages.success(request, 'Paylaşım kaldırıldı.')
    else:
        Activity.objects.create(
            user=request.user,
            action_type='SHARED',
            original_activity=target_activity,
            movie=target_activity.movie, # Filtreleme kolaylığı için kopyala
            book=target_activity.book
        )
        messages.success(request, 'Aktivite profilinizde paylaşıldı.')
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def movies_page(request):
    genre_id = request.GET.get('genre')
    genres = get_movie_genres()
    
    if genre_id:
        movies = get_movies_by_genre(genre_id)
        title = next((g['name'] for g in genres if str(g['id']) == genre_id), "Filmler")
    else:
        movies = get_popular_movies()
        title = "Popüler Filmler"
        
    # Local Top Rated
    local_top_movies = Movie.objects.annotate(
        avg_rating=Avg('rating__score'), 
        count=Count('rating')
    ).filter(count__gt=0).order_by('-avg_rating')[:5]

    context = {
        'movies': movies,
        'genres': genres,
        'title': title,
        'local_top_movies': local_top_movies,
        'is_genre_selected': bool(genre_id)
    }
    return render(request, 'movies.html', context)

def tv_series_page(request):
    genre_id = request.GET.get('genre')
    genres = get_tv_genres()
    
    if genre_id:
        tv_series = get_tv_series_by_genre(genre_id)
        title = next((g['name'] for g in genres if str(g['id']) == genre_id), "Diziler")
    else:
        tv_series = get_popular_tv_series()
        title = "Popüler Diziler"
    
    # Local Top Rated TV Series
    local_top_series = TVSeries.objects.annotate(
        avg_rating=Avg('rating__score'), 
        count=Count('rating')
    ).filter(count__gt=0).order_by('-avg_rating')[:5]

    context = {
        'tv_series': tv_series,
        'genres': genres,
        'title': title,
        'local_top_series': local_top_series,
        'is_genre_selected': bool(genre_id)
    }
    return render(request, 'tv_series.html', context)

def tv_series_detail(request, tmdb_id):
    tv_data = get_tv_series_detail_service(tmdb_id)
    if not tv_data:
        return redirect('index')

    tv_obj = TVSeries.objects.filter(tmdb_id=tmdb_id).first()
    
    reviews = []
    user_rating = None
    avg_rating = None # Varsayılan olarak None (Platform puanı yoksa - görünmesi için)
    
    if tv_obj:
        reviews = Review.objects.filter(tv_series=tv_obj).select_related('user', 'user__profile').order_by('-created_at')
        if request.user.is_authenticated:
            rating_obj = Rating.objects.filter(user=request.user, tv_series=tv_obj).first()
            if rating_obj:
                user_rating = rating_obj.score
        
        local_avg = Rating.objects.filter(tv_series=tv_obj).aggregate(Avg('score'))['score__avg']
        if local_avg:
            avg_rating = local_avg

    context = {
        'tv': tv_data,
        'tv_obj': tv_obj,
        'reviews': reviews,
        'user_rating': user_rating,
        'avg_rating': avg_rating,
    }
    return render(request, 'tv_series_detail.html', context)

def books_page(request):
    category = request.GET.get('category', 'fiction')
    # Google Books API için kategori eşleştirmeleri
    category_map = {
        'fiction': 'subject:fiction',
        'science': 'subject:science',
        'history': 'subject:history',
        'romance': 'subject:romance',
        'fantasy': 'subject:fantasy',
        'biography': 'subject:biography',
        'mystery': 'subject:mystery',
        'english_literature': 'subject:"English literature"',
        'self_help': 'subject:"self-help"',
        'scifi': 'subject:"science fiction"',
        'thriller': 'subject:thriller',
        'philosophy': 'subject:philosophy',
    }
    
    search_query = category_map.get(category, f'subject:{category}')
    books = get_books_by_category(search_query)
    
    # Categories
    categories = [
        {'id': 'fiction', 'name': 'Kurgu'},
        {'id': 'scifi', 'name': 'Bilim Kurgu'},
        {'id': 'fantasy', 'name': 'Fantastik'},
        {'id': 'mystery', 'name': 'Polisiye'},
        {'id': 'thriller', 'name': 'Gerilim'},
        {'id': 'romance', 'name': 'Romantik'},
        {'id': 'science', 'name': 'Bilim'},
        {'id': 'history', 'name': 'Tarih'},
        {'id': 'philosophy', 'name': 'Felsefe'},
        {'id': 'self_help', 'name': 'Kişisel Gelişim'},
        {'id': 'english_literature', 'name': 'İngiliz Edebiyatı'},
        {'id': 'biography', 'name': 'Biyografi'},
    ]
    
    # Local Top Rated
    local_top_books = Book.objects.annotate(
        avg_rating=Avg('rating__score'),
        count=Count('rating')
    ).filter(count__gt=0).order_by('-avg_rating')[:5]

    context = {
        'books': books,
        'categories': categories,
        'current_category': category,
        'local_top_books': local_top_books
    }
    return render(request, 'books.html', context)

def members_page(request):
    active_users = User.objects.filter(is_superuser=False).annotate(activity_count=Count('activities')).order_by('-activity_count')[:12]
    
    for user in active_users:
        user.movie_count = Activity.objects.filter(user=user, movie__isnull=False).count()
        user.book_count = Activity.objects.filter(user=user, book__isnull=False).count()
        user.review_count = Activity.objects.filter(user=user, action_type='REVIEWED').count()
        
        recent_activities = Activity.objects.filter(user=user).select_related('movie', 'book').order_by('-created_at')
        
        recent_items = []
        seen_ids = set()
        
        for activity in recent_activities:
            if len(recent_items) >= 4:
                break
                
            item_data = None
            unique_key = None
            
            if activity.movie:
                unique_key = f"movie_{activity.movie.id}"
                if unique_key not in seen_ids:
                    item_data = {
                        'type': 'movie',
                        'image': f"https://image.tmdb.org/t/p/w92{activity.movie.poster_path}",
                        'title': activity.movie.title
                    }
            elif activity.book:
                unique_key = f"book_{activity.book.id}"
                if unique_key not in seen_ids:
                    item_data = {
                        'type': 'book',
                        'image': activity.book.cover_path,
                        'title': activity.book.title
                    }
            
            if item_data:
                seen_ids.add(unique_key)
                recent_items.append(item_data)
        
        user.recent_items = recent_items

    popular_reviews = Activity.objects.filter(action_type='REVIEWED', user__is_superuser=False) \
        .exclude(related_review__isnull=True) \
        .exclude(related_review__text='') \
        .annotate(like_count=Count('likes')) \
        .order_by('-like_count')[:6]
    
    popular_activities = Activity.objects.filter(user__is_superuser=False).annotate(like_count=Count('likes')).filter(like_count__gt=0).order_by('-like_count')[:6]

    if request.user.is_authenticated:
        for activity in popular_reviews:
            activity.is_liked = activity.likes.filter(user=request.user).exists()
        
        for activity in popular_activities:
            activity.is_liked = activity.likes.filter(user=request.user).exists()

    context = {
        'active_users': active_users,
        'popular_reviews': popular_reviews,
        'popular_activities': popular_activities
    }
    return render(request, 'members.html', context)

def search_page(request):
    query = request.GET.get('q', '').strip()
    
    if not query:
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    results = search_content_service(query)
        
    return render(request, 'search_results.html', {'query': query, 'results': results})

@login_required
def notifications_page(request):
    notifications = request.user.notifications.all().select_related('sender', 'sender__profile', 'activity')
    
    # Template'de "Yeni" ibaresini göstermek için önce listeyi alıyoruz
    notifications_list = list(notifications)
    
    unread_notifications = request.user.notifications.filter(is_read=False)
    if unread_notifications.exists():
        unread_notifications.update(is_read=True)
        
    return render(request, 'notifications.html', {'notifications': notifications_list})

def lists_page(request):
    lists = UserList.objects.filter(list_type='custom').annotate(
        like_count=Count('likes')
    ).order_by('-like_count')
    
    for lst in lists:
        preview_items = []
        
        for m in lst.movies.all()[:5]:
            if m.poster_path:
                preview_items.append(f"https://image.tmdb.org/t/p/w154{m.poster_path}")
        
        if len(preview_items) < 5:
            remaining = 5 - len(preview_items)
            for t in lst.tv_series.all()[:remaining]:
                if t.poster_path:
                    preview_items.append(f"https://image.tmdb.org/t/p/w154{t.poster_path}")
                    
        if len(preview_items) < 5:
            remaining = 5 - len(preview_items)
            for b in lst.books.all()[:remaining]:
                if b.cover_path:
                    preview_items.append(b.cover_path)
        
        while len(preview_items) < 5:
            preview_items.append(None)
                    
        lst.preview_images = preview_items
        lst.is_liked = request.user.is_authenticated and lst.likes.filter(id=request.user.id).exists()

    return render(request, 'lists.html', {'lists': lists})

@login_required
def like_list(request, list_id):
    user_list = get_object_or_404(UserList, id=list_id)
    if user_list.likes.filter(id=request.user.id).exists():
        user_list.likes.remove(request.user)
        liked = False
    else:
        user_list.likes.add(request.user)
        liked = True
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'liked' if liked else 'unliked', 'like_count': user_list.likes.count()})
        
    return redirect(request.META.get('HTTP_REFERER', 'lists_page'))

@login_required
def add_item_to_list(request, list_id, item_type, item_id):
    user_list = get_object_or_404(UserList, id=list_id, user=request.user)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    try:
        if item_type == 'movie':
            # Önce DB'de var mı bak
            movie = Movie.objects.filter(tmdb_id=item_id).first()
            if not movie:
                # Yoksa TMDB'den çek ve kaydet
                details = get_movie_detail_service(item_id)
                if details:
                    release_date = details.get('release_date')
                    if not release_date: release_date = None
                    
                    movie = Movie.objects.create(
                        tmdb_id=details['id'],
                        title=details['title'],
                        overview=details.get('overview', ''),
                        poster_path=details.get('poster_path', ''),
                        release_date=release_date,
                        vote_average=details.get('vote_average', 0)
                    )
            
            if movie:
                user_list.movies.add(movie)
                return JsonResponse({'status': 'success'})
                
        elif item_type == 'tv':
            # Önce DB'de var mı bak
            tv = TVSeries.objects.filter(tmdb_id=item_id).first()
            if not tv:
                # Yoksa TMDB'den çek ve kaydet
                details = get_tv_series_detail_service(item_id)
                if details:
                    first_air_date = details.get('first_air_date')
                    if not first_air_date: first_air_date = None
                    
                    tv = TVSeries.objects.create(
                        tmdb_id=details['id'],
                        title=details['name'],
                        overview=details.get('overview', ''),
                        poster_path=details.get('poster_path', ''),
                        first_air_date=first_air_date,
                        vote_average=details.get('vote_average', 0)
                    )
            
            if tv:
                user_list.tv_series.add(tv)
                return JsonResponse({'status': 'success'})

        elif item_type == 'book':
            book = Book.objects.filter(google_id=item_id).first()
            if not book:
                details = get_book_detail_service(item_id)
                if details:
                    info = details.get('volumeInfo', {})
                    authors = ", ".join(info.get('authors', [])) if info.get('authors') else "Yazar Bilinmiyor"
                    cover = f"https://books.google.com/books/content?id={details['id']}&printsec=frontcover&img=1&zoom=1&h=1000&source=gbs_api"
                    
                    book = Book.objects.create(
                        google_id=details['id'],
                        title=info.get('title', 'Bilinmiyor'),
                        authors=authors,
                        description=info.get('description', ''),
                        cover_path=cover,
                        page_count=info.get('pageCount', 0)
                    )
            
            if book:
                user_list.books.add(book)
                return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Item not found'})

@login_required
def remove_item_from_list(request, list_id, item_type, item_id):
    user_list = get_object_or_404(UserList, id=list_id, user=request.user)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    try:
        if item_type == 'movie':
            # item_id artık TMDB ID olarak geliyor
            movie = get_object_or_404(Movie, tmdb_id=item_id)
            user_list.movies.remove(movie)
            
        elif item_type == 'tv':
            tv = get_object_or_404(TVSeries, tmdb_id=item_id)
            user_list.tv_series.remove(tv)
            
        elif item_type == 'book':
            book = get_object_or_404(Book, google_id=item_id)
            user_list.books.remove(book)
            
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})