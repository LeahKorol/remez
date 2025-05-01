from analysis.views import QueryViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"queries", QueryViewSet, basename="query")
urlpatterns = router.urls
