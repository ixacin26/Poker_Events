"""
URL configuration for poker_events project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from poker_events import views  # Import views from the appropriate directory

#TODO change url that is shown to "poker_events"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('add-event/', views.add_event, name='add_event'),
    path('add_players/<int:event_id>/', views.add_players, name='add_players'),
    path('end_event/<int:event_id>/', views.end_event, name='end_event'),
    path('re_buy/<int:event_id>/', views.re_buy, name='re_buy'),
]
