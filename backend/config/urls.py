from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from store.admin import my_admin
from store.views import health_check, system_status


def home_redirect(request):
    return redirect("/admin/")


urlpatterns = [
    path("",                    home_redirect),
    path("admin/",              my_admin.urls),
    path("api/health/",         health_check,    name="health_check"),
    path("api/status/",         system_status,   name="system_status"),
    path("api/token/",          TokenObtainPairView.as_view(),  name="token_obtain_pair"),
    path("api/token/refresh/",  TokenRefreshView.as_view(),     name="token_refresh"),
    path("api/",                include("store.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)