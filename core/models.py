from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# --- 1. PROFİL ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)

    def __str__(self):
        return self.user.username

# --- 2. İÇERİKLER ---
class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True)
    poster_path = models.CharField(max_length=255, blank=True)
    release_date = models.DateField(null=True, blank=True)
    vote_average = models.FloatField(default=0)

    def __str__(self):
        return self.title

class TVSeries(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True)
    poster_path = models.CharField(max_length=255, blank=True)
    first_air_date = models.DateField(null=True, blank=True)
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

# --- 3. ETKİLEŞİMLER ---
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    tv_series = models.ForeignKey(TVSeries, on_delete=models.CASCADE, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'movie'], ['user', 'book'], ['user', 'tv_series']]

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    tv_series = models.ForeignKey(TVSeries, on_delete=models.CASCADE, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# --- 4. AKTİVİTE AKIŞI ---
class Activity(models.Model):
    ACTION_TYPES = (
        ('RATED', 'Puanladı'),
        ('REVIEWED', 'Yorumladı'),
        ('ADDED_LIST', 'Listeye Ekledi'),
        ('SHARED', 'Paylaştı'),
        ('COMMENTED', 'Yorum Yaptı'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    tv_series = models.ForeignKey(TVSeries, on_delete=models.CASCADE, null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    
    related_rating = models.ForeignKey(Rating, on_delete=models.SET_NULL, null=True, blank=True)
    related_review = models.ForeignKey(Review, on_delete=models.SET_NULL, null=True, blank=True)
    related_list = models.ForeignKey('UserList', on_delete=models.SET_NULL, null=True, blank=True)
    related_comment = models.ForeignKey('ActivityComment', on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_reference')
    
    original_activity = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='shares')
    
    class Meta:
        ordering = ['-created_at']

class ActivityLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'activity')

class ActivityComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('FOLLOW', 'Takip'),
        ('LIKE', 'Beğeni'),
        ('COMMENT', 'Yorum'),
    )
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# --- 5. LİSTELER ---
class UserList(models.Model):
    LIST_TYPES = (
        ('watched', 'İzledim'),
        ('watchlist', 'İzlenecek'),
        ('read', 'Okudum'),
        ('readlist', 'Okunacak'),
        ('custom', 'Özel Liste'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lists')
    name = models.CharField(max_length=100)
    list_type = models.CharField(max_length=20, choices=LIST_TYPES, default='custom')
    
    movies = models.ManyToManyField(Movie, blank=True, related_name='lists')
    tv_series = models.ManyToManyField(TVSeries, blank=True, related_name='lists')
    books = models.ManyToManyField(Book, blank=True, related_name='lists')
    
    likes = models.ManyToManyField(User, related_name='liked_lists', blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"
