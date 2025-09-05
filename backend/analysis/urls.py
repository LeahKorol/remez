from analysis.views import QueryViewSet, DrugNameViewSet, ReactionNameViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"queries", QueryViewSet, basename="query")
router.register(r"drug-names", DrugNameViewSet, basename="drug-name")
router.register(r"reaction-names", ReactionNameViewSet, basename="reaction-name")
urlpatterns = router.urls

from django.urls import path
from . import chart_views

urlpatterns = [
    path('queries/<int:query_id>/chart/', chart_views.serve_chart, name='serve_chart'),
    path('queries/<int:query_id>/data/', chart_views.get_chart_data, name='get_chart_data'),
    path('queries/<int:query_id>/results/', chart_views.query_results, name='query_results'),
]