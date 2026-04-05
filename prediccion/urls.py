from django.urls import path
from prediccion import views
from django.contrib.auth import views as auth_views
 
urlpatterns = [
    # ── Públicas ──────────────────────────────────────────
    path('', views.landing, name='landing'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('registro/', views.registro, name='registro'),
    path('cerrar-sesion/', views.cerrar_sesion, name='cerrar_sesion'),
 
    # ── Autenticadas ──────────────────────────────────────
    path('home/', views.home, name='home'),
    path('lectura/', views.register_reading, name='register_reading'),
    path('lectura/<int:pk>/resultado/', views.reading_result, name='reading_result'),
    path('historial/', views.history, name='history'),
]