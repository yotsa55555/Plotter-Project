# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('data/', views.data, name='data'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('contact/', views.contact, name='contact'),
    path('describe', views.describe_data, name='describe'),
    path('selectPlot', views.select_viz, name='selectPlot'),
    path('bar', views.bar_viz, name='bar'),
    path('box', views.box_viz, name='box'),
    path('histogram', views.histogram_viz, name='histogram'),
    path('pie', views.pie_viz, name='pie'),
    path('scatter', views.scatter_viz, name='scatter'),
    path('line', views.line_viz, name='line'),
    path('export/', views.export_plots, name='export_plots'),
]
