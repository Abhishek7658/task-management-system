from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from accounts.views import RegistrationView, UserViewSet
from teams.views import TeamViewSet
from projects.views import ProjectViewSet
from tasks.views import TaskViewSet
from activity.views import DashboardView

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("teams", TeamViewSet, basename="team")
router.register("projects", ProjectViewSet, basename="project")
router.register("tasks", TaskViewSet, basename="task")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/register/", RegistrationView.as_view(), name="register"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/dashboard/", DashboardView.as_view(), name="dashboard"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/", include(router.urls)),
]
