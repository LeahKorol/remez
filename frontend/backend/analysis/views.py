from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.response import Response
from analysis.models import Query
from analysis.serializers import QuerySerializer
from drf_spectacular.utils import extend_schema_view, extend_schema
from django.shortcuts import get_object_or_404


@extend_schema_view(
    **{
        method: extend_schema(tags=["Analysis"])
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
