import logging
import os
import subprocess
import sys
from datetime import datetime

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from analysis.constants import PIPELINE_DEMO_DATA
from analysis.models import DrugName, Query, ReactionName
from analysis.serializers import (
    DrugNameSerializer,
    QuerySerializer,
    ReactionNameSerializer,
)

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
        return Query.objects.filter(user=self.request.user)

    def get_object(self):
        """Single database lookup for single-obkect queries"""
        return get_object_or_404(Query, user=self.request.user, id=self.kwargs["id"])

    def perform_create(self, serializer):
        """
        Override perform_create method to automatically assign the authenticated user and calculate ror results.
        DRF calls serializer.is_valid() before perform_create is invoked.
        Pass the calculated results and the user as additional fields to serializer.save().
        If settings.NUM_DEMO_QUARTERS is set to a value between 0 and 4, use demo data for the results.
        """
        # save the user because it's a create operation
        save_kwards = {"user": self.request.user}
        if settings.NUM_DEMO_QUARTERS >= 0:
            save_kwards.update(self.get_demo_data())
        else:
            # Calculate ror_values, ror_lower, ror_upper
            try:
                # Use the same Python executable that Django is using
                python_executable = sys.executable

                # Get project root dynamically
                project_root = getattr(
                    settings,
                    "BASE_DIR",
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                )

                # Build pipeline script path relative to project root
                pipeline_script = os.path.join(
                    project_root, "analysis", "pipeline", "pipeline.py"
                )

                year_start = serializer.validated_data["year_start"]
                year_end = serializer.validated_data["year_end"]

                querter_start = serializer.validated_data["quarter_start"]
                quarter_end = serializer.validated_data["quarter_end"]

                year_q_from = f"{year_start}q{querter_start}"
                year_q_to = f"{year_end}q{quarter_end}"

                logger.debug("year_q_from: {year_q_from}")
                logger.debug("year_q_to: {year_q_to}")

                cmd = [
                    python_executable,
                    pipeline_script,
                    "Faers_Pipeline",
                    f"--Faers-Pipeline-year-q-from={year_q_from}",
                    f"--Faers-Pipeline-year-q-to={year_q_to}",
                ]

                logger.debug(f"Using Python: {python_executable}")
                logger.debug(f"Project root: {project_root}")
                logger.debug(f"Pipeline script: {pipeline_script}")
                logger.info(f"Starting Luigi pipeline: {' '.join(cmd)}")

                # Redirect output to file
                log_filename = (
                    f"luigi_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                )
                log_file = open(log_filename, "w")

                process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=log_file,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=project_root,  # This fixes the relative path issue, so the pipeline can use absolute paths
                )

                logger.info(f"Luigi pipeline started with PID: {process.pid}")
                logger.debug("Check output in: luigi_pipeline.log")
            except Exception as e:
                raise RuntimeError(f"Error running luigi pipeline: {e}")

        serializer.save(**save_kwards)

    def perform_update(self, serializer):
        """
        Override perform_update method to calculate ror results.
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

        save_kwards = {}
        if settings.NUM_DEMO_QUARTERS >= 0:
            save_kwards.update(self.get_demo_data())
        else:
            # TO-DO: Recalculate ror_values, ror_lower, ror_upper
            pass

        serializer.save(**save_kwards)

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
