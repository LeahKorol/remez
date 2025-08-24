from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from analysis.models import Query, DrugName, ReactionName
from analysis.serializers import (
    QuerySerializer,
    DrugNameSerializer,
    ReactionNameSerializer,
)
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from django.shortcuts import get_object_or_404


@extend_schema_view(
    **{
        method: extend_schema(tags=["Query"])
        for method in [
            "list",
            "retrieve",
            "create",
            "update",
            "partial_update",
            "destroy",
        ]
    }
)
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
        """Override perform_create method to automatically assign the authenticated user and calculate results."""
        # TO-DO: Calculate x_values and y_values
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Override perform_update method to calculate results."""
        # TO-DO: Recalculate x_values and y_values
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        "Ensure partial updates are allowed when calling PATCH requests"
        kwargs["partial"] = True

        # Serialize and validate request data
        serializer = self.get_serializer(
            instance=self.get_object(), data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        # Modify results if relevant fields were changed
        validated_data = serializer.validated_data
        if (
            any(
                (
                    "drugs",
                    "reactions",
                    "quarter_start",
                    "quarter_end",
                    "year_star",
                    "year_end",
                )
            )
            in validated_data
        ):
            # TO-DO: Recalaculte x_values and y_values
            pass

        # Save the data
        serializer.save(**validated_data)
        return Response(data=serializer.data)

    @action(detail=False, methods=["get"], url_path="queries-names")
    def get_queries_names(self, request):
        """
        Retrieves all queries names for the authenticated user.
        """
        queries = self.get_queryset()
        query_names = queries.values_list("name", flat=True)
        return Response(query_names, status=status.HTTP_200_OK)


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
        tags=["Drug Names"]
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
