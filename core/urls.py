from django.contrib import admin
from django.urls import path, include
from django.conf import settings # YENİ
from django.conf.urls.static import static # YENİ
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from core.views import (
    MovieViewSet, BookViewSet, FeedViewSet, SearchView, 
    index, register_view, login_view, logout_view, movie_detail, 
    profile_view, edit_profile_view, MovieInteractionView, book_detail, follow_user,
    create_custom_list, list_detail, remove_follower,
    add_rating, add_review, delete_review, edit_review,
    like_activity, add_activity_comment, share_activity,
    movies_page, books_page, members_page, search_page, explore, filter_content, notifications_page # YENİ
)

# API Router
router = DefaultRouter()
router.register(r'movies', MovieViewSet)
router.register(r'books', BookViewSet)
router.register(r'feed', FeedViewSet, basename='feed') 

urlpatterns = [
    path('', index, name='home'),
    path('explore/', explore, name='explore'), # YENİ
    path('explore/filter/', filter_content, name='filter_content'), # YENİ
    path('movies/', movies_page, name='movies_page'),
    path('books/', books_page, name='books_page'),
    path('members/', members_page, name='members_page'),
    path('search/', search_page, name='search_page'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Şifre Sıfırlama
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html', email_template_name='password_reset_email.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

    path('movie/<int:tmdb_id>/', movie_detail, name='movie_detail'),
    path('book/<str:google_id>/', book_detail, name='book_detail'),
    
    # Profil Yolları
    path('profile/edit/', edit_profile_view, name='edit_profile'), # YENİ
    path('profile/create_list/', create_custom_list, name='create_custom_list'),
    path('list/<int:list_id>/', list_detail, name='list_detail'), # YENİ
    path('profile/<str:username>/', profile_view, name='profile'),
    path('profile/<str:username>/follow/', follow_user, name='follow_user'), # YENİ
    path('profile/<str:username>/remove_follower/', remove_follower, name='remove_follower'), # YENİ

    # Etkileşim API
    path('api/interact/', MovieInteractionView.as_view(), name='movie_interaction'),
    path('rating/add/', add_rating, name='add_rating'), # YENİ
    path('review/add/', add_review, name='add_review'), # YENİ
    path('review/edit/<int:review_id>/', edit_review, name='edit_review'), # YENİ
    path('review/delete/<int:review_id>/', delete_review, name='delete_review'), # YENİ
    
    # Aktivite Etkileşimleri
    path('activity/like/<int:activity_id>/', like_activity, name='like_activity'),
    path('activity/comment/<int:activity_id>/', add_activity_comment, name='add_activity_comment'),
    path('activity/share/<int:activity_id>/', share_activity, name='share_activity'),

    # Bildirimler
    path('notifications/', notifications_page, name='notifications_page'),

    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/search/', SearchView.as_view(), name='search'),
] 

# RESİMLERİN GÖRÜNMESİ İÇİN BU KOD ŞART:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)