from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Movie, Book, Rating, Review, Activity

# Kullanıcı Bilgisi
class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']

    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            return obj.profile.avatar.url
        return None

# Film ve Kitap
class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = '__all__'

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

# Sosyal Akış (Feed) için Aktivite Kartı
class ActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    movie = MovieSerializer(read_only=True)
    book = BookSerializer(read_only=True)
    
    # Ekstra bilgiler (Puanı ve Yorumu)
    rating_score = serializers.SerializerMethodField()
    review_preview = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = ['id', 'user', 'action_type', 'created_at', 'movie', 'book', 'rating_score', 'review_preview']

    def get_rating_score(self, obj):
        if obj.related_rating:
            return obj.related_rating.score
        return None

    def get_review_preview(self, obj):
        if obj.related_review:
            # Yorumun sadece ilk 150 karakteri (PDF Madde 50)
            return obj.related_review.text[:150] + "..." 
        return None