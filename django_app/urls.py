from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_chart, name='upload_chart'),
    path('analysis/<uuid:chart_id>/', views.view_analysis, name='view_analysis'),
    path('gallery/', views.gallery, name='gallery'),
    path('api/analysis/<uuid:chart_id>/', views.api_analysis, name='api_analysis'),
]