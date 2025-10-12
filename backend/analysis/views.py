import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from analysis.constants import PIPELINE_DEMO_DATA
from analysis.models import DrugName, Query, ReactionName, Result, ResultStatus
from analysis.permissions import IsPipelineService
from analysis.serializers import (
    DrugNameSerializer,
    QuerySerializer,
    ReactionNameSerializer,
    ResultSerializer,
)
from analysis.services.pipeline_service import pipeline_service

logger = logging.getLogger(__name__)

query_schemas = {
    method: extend_schema(
        tags=["Query"],
        parameters=[
            OpenApiParameter(name="id", type=int, location=OpenApiParameter.PATH)
        ],
    )
    for method in [
        "retrieve",
        "update",
        "partial_update",
        "destroy",
    ]
}
for method in ["list", "create", "get_queries_names"]:
    query_schemas[method] = extend_schema(tags=["Query"])


@extend_schema_view(**query_schemas)
class QueryViewSet(viewsets.ModelViewSet):
    serializer_class = QuerySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"  # Force DRF to use "id" instead of "pk"

    def get_queryset(self):
        """Only return queries owned by the authenticated user."""
        # Optimize queries with related objects:
        # select_related for one-to-one or foreign key relationships
        # prefetch_related for many-to-many or reverse foreign key relationships
        return (
            Query.objects.filter(user=self.request.user)
            .select_related("result")
            .prefetch_related("drugs", "reactions")
        )

    def get_object(self):
        """Single database lookup for single-object queries"""
        return get_object_or_404(Query, user=self.request.user, id=self.kwargs["id"])

    def perform_create(self, serializer):
        """
        Override perform_create method to automatically assign the authenticated user and trigger pipeline analysis.
        DRF calls serializer.is_valid() before perform_create is invoked.
        Creates Query and Result objects both and calls pipeline service.
        If settings.NUM_DEMO_QUARTERS is set to a value between 0 and 4, use demo data for the results.
        """
        # Create Query with user assigned (as it is a create operation)
        query = serializer.save(user=self.request.user)

        # Handle demo data mode
        if settings.NUM_DEMO_QUARTERS >= 0:
            self._create_demo_result(query)
        else:
            # Trigger pipeline service for real analysis
            self._trigger_pipeline_analysis(query, serializer.validated_data)

    def perform_update(self, serializer):
        """
        Override perform_update method to trigger recalculation when relevant fields change.
        DRF calls serializer.is_valid() before perform_update is invoked.
        If settings.NUM_DEMO_QUARTERS is set to a value between 0 and 4, use demo data for the results.
        """
        recalculate_ror_fields = [
            "year_start",
            "year_end",
            "quarter_start",
            "quarter_end",
            "drugs",
            "reactions",
        ]
        if not any(field in self.request.data for field in recalculate_ror_fields):
            # No relevant fields updated, skip recalculation
            serializer.save()
            return

        # Save the query first
        query = serializer.save()

        # Handle demo data mode or trigger pipeline
        if settings.NUM_DEMO_QUARTERS >= 0:
            self._create_demo_result(query)
        else:
            self._trigger_pipeline_analysis(query, serializer.validated_data)

    def _create_demo_result(self, query):
        """Create Result object with demo data and mark as completed."""
        try:
            demo_data = self.get_demo_data()

            # Update the result created by serializer with demo data
            result = query.result
            result.status = ResultStatus.COMPLETED
            result.ror_values = demo_data["ror_values"]
            result.ror_lower = demo_data["ror_lower"]
            result.ror_upper = demo_data["ror_upper"]
            result.save()

            logger.info(f"Demo result created for query {query.id}")

        except Exception as e:
            logger.error(f"Error creating demo result for query {query.id}: {str(e)}")
            # Keep result in PENDING status if demo creation fails

    def _trigger_pipeline_analysis(self, query, validated_data):
        """Trigger pipeline analysis for the query."""
        try:
            # Mark result as pending
            result = query.result
            result.status = ResultStatus.PENDING
            result.save()

            # Prepare data for pipeline service
            drugs = list(query.drugs.all())
            reactions = list(query.reactions.all())

            # Use current query values for parameters not in validated_data (for updates)
            year_start = validated_data.get("year_start", query.year_start)
            year_end = validated_data.get("year_end", query.year_end)
            quarter_start = validated_data.get("quarter_start", query.quarter_start)
            quarter_end = validated_data.get("quarter_end", query.quarter_end)

            # Call pipeline service
            pipeline_service.trigger_pipeline_analysis(
                drugs=drugs,
                reactions=reactions,
                result_id=result.id,
                year_start=year_start,
                year_end=year_end,
                quarter_start=quarter_start,
                quarter_end=quarter_end,
            )

            logger.info(
                f"Pipeline analysis triggered for query {query.id}, result {result.id}"
            )

        except Exception as e:
            logger.error(
                f"Error triggering pipeline analysis for query {query.id}: {str(e)}"
            )
            # Mark result as failed
            try:
                result = query.result
                result.status = ResultStatus.FAILED
                result.save()
            except Exception as e:
                logger.error(
                    f"Error updating result status for query {query.id}: {str(e)}"
                )
                # Don't fail on result update error

            raise  # Re-raise to let DRF handle the error response

    @action(detail=False, methods=["get"], url_path="queries-names")
    def get_queries_names(self, request):
        """
        Retrieves all queries names for the authenticated user.
        """
        queries = self.get_queryset()
        query_names = queries.values_list("name", flat=True)
        return Response(query_names, status=status.HTTP_200_OK)

    def get_demo_data(self):
        if settings.NUM_DEMO_QUARTERS not in range(0, 5):
            raise ValueError("NUM_DEMO_QUARTERS must be between 0 and 4")

        demo_data = PIPELINE_DEMO_DATA[settings.NUM_DEMO_QUARTERS]
        demo_data_kwargs = {
            "ror_values": demo_data["ror_values"],
            "ror_lower": demo_data["ror_lower"],
            "ror_upper": demo_data["ror_upper"],
        }
        return demo_data_kwargs


@extend_schema_view(
    retrieve=extend_schema(
        tags=["Result"],
        parameters=[
            OpenApiParameter(name="id", type=int, location=OpenApiParameter.PATH)
        ],
    ),
    list=extend_schema(tags=["Result"]),
    update_by_task_id=extend_schema(
        tags=["Result"],
        parameters=[
            OpenApiParameter(name="task_id", type=str, location=OpenApiParameter.PATH)
        ],
        description="Update result by task_id. Used by external pipeline service.",
    ),
)
class ResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Result model with the following access rules:
    - Regular users: read-only access to their own results via query__user
    - Pipeline service: can update results using task_id (currently same as pk)
    - No one can create or delete results through this API
    """

    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"  # Force DRF to use "id" instead of "pk"

    def get_queryset(self):
        """
        Filter results to only show those belonging to the authenticated user.
        Use select_related to optimize queryset by joining the related Query in one DB hit.
        It Prevents N+1 queries when accessing query fields in results (as query__user).
        The user still only sees the fields defined in the serializer, not all query data.
        """
        return Result.objects.filter(query__user=self.request.user).select_related(
            "query"
        )

    @action(
        detail=False,
        methods=["put"],
        url_path="update-by-task/(?P<task_id>[^/.]+)",
        permission_classes=[IsPipelineService],
    )
    def update_by_task_id(self, request, task_id):
        """
        Custom endpoint for external service to update results using task_id.
        The task_id is currently the same as the Result's pk.
        We use custom endpoint and not default update to decouple external usage from internal URLs.
        In addition, it allows flexibility to use different task_id than pk without affecting the integration.
        URL: /results/update-by-task/{task_id}/
        Method: PUT (full update is required)

        Protected by IsPipelineService permission (IP whitelist).
        """
        # check if task_id is a valid django model id
        if not task_id.isdigit():
            return Response(
                {"error": "Invalid task_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = Result.objects.get(id=task_id)
        except Result.DoesNotExist:
            logger.warning(f"No result was found for id {task_id}")
            return Response(
                {"error": "Result not found for this task_id"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(result, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info(f"Result {result.id} is updated by task_id {task_id}")

        return Response(serializer.data)


class TermNameSearchViewSet(viewsets.GenericViewSet):
    """Base viewset for searching term names by prefix."""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="search/(?P<prefix>[^/.]+)")
    def search_by_prefix(self, request, prefix=None):
        # Input validation
        if not isinstance(prefix, str):
            return Response(
                {"error": "Invalid prefix type"}, status=status.HTTP_400_BAD_REQUEST
            )

        prefix = prefix.strip()
        if len(prefix) < 3:
            return Response(
                {"error": "Prefix must be at least 3 characters long"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Perform case-insensitive search
        term_names = self.queryset.filter(name__istartswith=prefix).order_by("name")[
            :100
        ]
        if not term_names.exists():
            return Response(
                {"message": f"No matching term {self.model_name} found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Handle pagination
        page = self.paginate_queryset(term_names)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(term_names, many=True)
        return Response(serializer.data)


@extend_schema_view(
    search_by_prefix=extend_schema(
        tags=["Drug Names"],
        parameters=[
            OpenApiParameter(
                name="prefix", type="string", location=OpenApiParameter.PATH
            )
        ],
    )
)
class DrugNameViewSet(TermNameSearchViewSet):
    serializer_class = DrugNameSerializer
    queryset = DrugName.objects.all()
    model_name = "drug name"


@extend_schema_view(
    search_by_prefix=extend_schema(
        tags=["Reaction Names"],
        parameters=[{"name": "prefix", "in": "path", "type": "string"}],
    )
)
class ReactionNameViewSet(TermNameSearchViewSet):
    serializer_class = ReactionNameSerializer
    queryset = ReactionName.objects.all()
    model_name = "reaction name"
