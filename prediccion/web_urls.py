from django.urls import path
from . import web_views

app_name = 'web'

urlpatterns = [
    path('login/',    web_views.web_login,     name='login'),
    path('logout/',   web_views.web_logout,    name='logout'),
    path('',          web_views.dashboard,     name='dashboard'),
    path('eda/',      web_views.eda,           name='eda'),
    path('users/',    web_views.users_view,    name='users'),
    path('readings/', web_views.readings_view, name='readings'),
    path('riesgo/',   web_views.risk_panel,   name='risk'),
    path('digital-twin/', web_views.digital_twin, name='digital-twin'),
]