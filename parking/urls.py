from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('entry/', views.entry_view, name='entry'),
    path('exit/', views.exit_view, name='exit'),
    path('zones/', views.zones_view, name='zones'),
    path('reports/', views.reports_view, name='reports'),
    path('logs/', views.vehicle_log_view, name='logs'),
    path('settings/', views.settings_view, name='settings'),
]
