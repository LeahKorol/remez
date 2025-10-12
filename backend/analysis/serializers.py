from django.db import transaction
from rest_framework import serializers

from analysis.models import DrugName, Query, ReactionName, Result, ResultStatus


class DrugNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrugName
        fields = "__all__"
        read_only_fields = ("id", "name")


class ReactionNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReactionName
        fields = "__all__"
        read_only_fields = ("id", "name")


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = "__all__"
        read_only_fields = ("id", "query")


class QuerySerializer(serializers.ModelSerializer):
    # Write-only fields: Accept simple IDs for input (POST/PUT/PATCH)
    drugs = serializers.PrimaryKeyRelatedField(
        many=True, queryset=DrugName.objects.all(), write_only=True
    )
    reactions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ReactionName.objects.all(), write_only=True
    )

    # Read-only fields: Return full nested objects for output (GET responses)
    # Return lists of drugs and reactions with their details (id and name) instead of just IDs
    # provided by default PrimarKeyRelatedField. It prevents additional queries to get the terms names.
    drugs_details = DrugNameSerializer(source="drugs", many=True, read_only=True)
    reactions_details = ReactionNameSerializer(
        source="reactions", many=True, read_only=True
    )
    result = ResultSerializer(read_only=True)

    class Meta:
        model = Query
        fields = "__all__"
        read_only_fields = (
            "id",
            "user",
            "created_at",
            "updated_at",
            "drugs_details",
            "reactions_details",
            "result",
        )

    def validate(self, data):
        """Ensure drugs & reactions are not empty lists and validate quarter/year combinations."""
        if "drugs" in data and not data["drugs"]:
            raise serializers.ValidationError(
                {"drugs": "At least one drug is required."}
            )
        if "reactions" in data and not data["reactions"]:
            raise serializers.ValidationError(
                {"reactions": "At least one reaction is required."}
            )

        if (
            "year_start" in data
            and "year_end" in data
            and data["year_start"] > data["year_end"]
        ):
            raise serializers.ValidationError(
                {"year_start": "year_start cannot be greater than year_end"}
            )

        if all(
            key in data
            for key in ["quarter_start", "quarter_end", "year_start", "year_end"]
        ):
            if (
                data["year_start"] == data["year_end"]
                and data["quarter_start"] >= data["quarter_end"]
            ):
                raise serializers.ValidationError(
                    {
                        "quarter_start": "quarter_start must be less than quarter_end within the same year"
                    }
                )
        return data

    def create(self, validated_data):
        """
        Creates a new Query instance with associated drugs and reactions.
        Also creates the associated Result object in PENDING status.
        This method handles the atomic creation of both objects along with
        many-to-many relationships.
        """
        drugs = validated_data.pop("drugs")
        reactions = validated_data.pop("reactions")

        with transaction.atomic():
            query = Query.objects.create(**validated_data)
            query.drugs.set(drugs)
            query.reactions.set(reactions)

            # Create associated Result object in PENDING status
            Result.objects.create(query=query, status=ResultStatus.PENDING)

            return query
        return None

    def update(self, instance, validated_data):
        """
        Updates an instance with validated data, handling drug and reaction relationships atomically.
        Validates that new quarter/year values don't exceed existing ones when only those fields are updated.
        """
        # Check if quarter/year fields are being updated
        quarter_year_fields = {"quarter_start", "quarter_end", "year_start", "year_end"}
        updated_quarter_year_fields = set(validated_data.keys())

        if updated_quarter_year_fields.issubset(quarter_year_fields):
            year_start = validated_data.get("year_start", instance.year_start)
            year_end = validated_data.get("year_end", instance.year_end)
            quarter_start = validated_data.get("quarter_start", instance.quarter_start)
            quarter_end = validated_data.get("quarter_end", instance.quarter_end)

            # Compare new values with existing ones
            if year_start > year_end:
                raise serializers.ValidationError(
                    {
                        "year_start": "year_start cannot be greater than existing year_end"
                    }
                )

            if quarter_end <= quarter_start and year_start == year_end:
                raise serializers.ValidationError(
                    {
                        "quarter_start": "quarter_start must be less than existing quarter_end within the same year"
                    }
                )

        return super().update(instance, validated_data)
