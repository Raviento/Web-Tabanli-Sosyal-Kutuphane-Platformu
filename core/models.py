from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# --- 1. PROFİL (PDF: 2.1.5) ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)

    def __str__(self):
        return self.user.username

# --- 2. İÇERİKLER (PDF: 2.2.1) ---
class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True)
    poster_path = models.CharField(max_length=255, blank=True)
    release_date = models.DateField(null=True, blank=True)
    vote_average = models.FloatField(default=0)

    def __str__(self):
        return self.title

class Book(models.Model):
    google_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=500) 
    authors = models.TextField(blank=True)   
    description = models.TextField(blank=True)
    cover_path = models.TextField(blank=True) 
    page_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title

# --- 3. ETKİLEŞİMLER (PDF: 2.1.2) ---
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'movie'], ['user', 'book']]

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# --- 4. AKTİVİTE AKIŞI / FEED (PDF: 2.1.2) ---
class Activity(models.Model):
    ACTION_TYPES = (
        ('RATED', 'Puanladı'),
        ('REVIEWED', 'Yorumladı'),
        ('ADDED_LIST', 'Listeye Ekledi'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    
    related_rating = models.ForeignKey(Rating, on_delete=models.SET_NULL, null=True, blank=True)
    related_review = models.ForeignKey(Review, on_delete=models.SET_NULL, null=True, blank=True)

    related_list = models.ForeignKey('UserList', on_delete=models.SET_NULL, null=True, blank=True) 
    class Meta:
        ordering = ['-created_at']

# --- 5. LİSTELER (PDF: 2.1.4 & 2.1.5 - EKSİK OLAN KISIM) ---
class UserList(models.Model):
    LIST_TYPES = (
        ('watched', 'İzledim'),
        ('watchlist', 'İzlenecek'),
        ('read', 'Okudum'),
        ('readlist', 'Okunacak'),
        ('custom', 'Özel Liste'), # Kullanıcının oluşturduğu 'En İyi Filmler' vb.
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lists')
    name = models.CharField(max_length=100) # Liste adı
    list_type = models.CharField(max_length=20, choices=LIST_TYPES, default='custom')
    
    # Listenin içindekiler (Hem film hem kitap olabilir)
    movies = models.ManyToManyField(Movie, blank=True, related_name='lists')
    books = models.ManyToManyField(Book, blank=True, related_name='lists')

    def __str__(self):
        return f"{self.user.username} - {self.name}"
    