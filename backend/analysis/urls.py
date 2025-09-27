from analysis.views import QueryViewSet, DrugNameViewSet, ReactionNameViewSet, ResultViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"queries", QueryViewSet, basename="query")
router.register(r"results", ResultViewSet, basename="result")
router.register(r"drug-names", DrugNameViewSet, basename="drug-name")
router.register(r"reaction-names", ReactionNameViewSet, basename="reaction-name")
urlpatterns = router.urls