"""
URL configuration for MoneyFlowAPI project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include

URL_START_DIR = 'moneyflow/'

admin.site.site_header = 'MoneyFlow Admin'
admin.site.index_title = 'Manage Data & Permissions'

urlpatterns = [
    path(URL_START_DIR + 'admin/', admin.site.urls),
    path(URL_START_DIR, include('core.urls')),
    path(URL_START_DIR + 'account/', include('moneyflow.urls_account')),
    path(URL_START_DIR + 'creditcard/', include('moneyflow.urls_cc')),
    path(URL_START_DIR + 'tags/', include('tags.urls')),
]
