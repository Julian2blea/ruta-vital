from django.urls import path
from prediccion import views
from django.contrib.auth import views as auth_views

urlpatterns = [ 
    path('', views.landing, name='landing'),  
    path('home/', views.home, name='home'),  
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('registro/', views.registro, name='registro'),
    path('cuestionario/', views.procesar_cuestionario, name='cuestionario'),
    path('cerrar-sesion/', views.cerrar_sesion, name='cerrar_sesion'),
]
