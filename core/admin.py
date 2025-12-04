from django.contrib import admin
from .models import Profile, Movie, Book, Activity, UserList, Rating, Review, TVSeries

# Tabloları Admin Paneline Ekliyoruz
admin.site.register(Profile)
admin.site.register(Movie)
admin.site.register(TVSeries)
admin.site.register(Book)
admin.site.register(Activity)
admin.site.register(UserList)
admin.site.register(Rating)
admin.site.register(Review)