from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('generate_cv/', views.scrape_and_generate_cv, name='generate_cv'),
]
