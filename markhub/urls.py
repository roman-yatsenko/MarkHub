"""markhub URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path, include, re_path

from .views import HomeView, RepoView, FileView
from .views import new_file_ctr, update_file_ctr, delete_file_ctr

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('file/<slug:repo>/<path:path>/', FileView.as_view(), name='file'),
    path('delete-file/<slug:repo>/<path:path>/', delete_file_ctr, name='delete-file'),
    path('new-file/<slug:repo>/<path:path>/', new_file_ctr, name='new-file'),
    path('new-file/<slug:repo>/', new_file_ctr, name='new-file'),
    path('repo/<slug:repo>/<path:path>/', RepoView.as_view(), name='repo'),
    re_path(r'repo/(?P<repo>[-a-zA-Z0-9_/.]+)/$', RepoView.as_view(), name='repo'),
    path('update-file/<slug:repo>/<path:path>/', update_file_ctr, name='update-file'),
    path('', HomeView.as_view(), name='home'),
]
