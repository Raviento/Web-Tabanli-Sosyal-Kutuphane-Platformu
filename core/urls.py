from django.contrib import admin
from django.urls import path, include
from django.conf import settings # YENİ
from django.conf.urls.static import static # YENİ
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from core.views import (
    MovieViewSet, BookViewSet, FeedViewSet, SearchView, 
    index, register_view, login_view, logout_view, movie_detail, 
    profile_view, edit_profile_view, MovieInteractionView, book_detail
)

# API Router
router = DefaultRouter()
router.register(r'movies', MovieViewSet)
router.register(r'books', BookViewSet)
router.register(r'feed', FeedViewSet, basename='feed') 

urlpatterns = [
    path('', index, name='home'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('movie/<int:tmdb_id>/', movie_detail, name='movie_detail'),
    path('book/<str:google_id>/', book_detail, name='book_detail'),
    
    # Profil Yolları
    path('profile/edit/', edit_profile_view, name='edit_profile'), # YENİ
    path('profile/<str:username>/', profile_view, name='profile'),

    # Etkileşim API
    path('api/interact/', MovieInteractionView.as_view(), name='movie_interact'),

    # Şifre Sıfırlama
    path('reset_password/', auth_views.PasswordResetView.as_view(), name='reset_password'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/search/', SearchView.as_view(), name='search'),
] 

# RESİMLERİN GÖRÜNMESİ İÇİN BU KOD ŞART:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)