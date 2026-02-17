from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from apps.budgets.views import inscription
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('manager/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),

    # Authentification
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/inscription/', inscription, name='inscription'),

    # Applications
    path('budgets/', include('apps.budgets.urls')),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)