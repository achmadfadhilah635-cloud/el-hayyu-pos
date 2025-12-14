from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views 
from apps.pages import views as pages_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. MENU UTAMA
    path('', pages_views.index, name='index'),
    path('billing/', pages_views.billing, name='billing'),
    path('analytics/', pages_views.analytics, name='analytics'),
    path('profile/', pages_views.profile, name='profile'),
    
    # 2. LOGIN & REGISTER
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html')),
    path('register/', pages_views.register, name='register'),
    
    # --- [PENTING] PERBAIKAN LOGOUT ---
    # Taruh INI SEBELUM 'django.contrib.auth.urls'
    # Supaya link logout Mas tidak kena Error 405
    path('logout/', pages_views.logout_view, name='logout'),
    path('accounts/logout/', pages_views.logout_view), # Kita bajak juga jalur bawaannya
    
    # 3. SISA FITUR BAWAAN
    path('accounts/', include('django.contrib.auth.urls')),

    # 4. APLIKASI
    path('analysis/', include('apps.charts.urls')), 
    path('', include('apps.dyn_dt.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)