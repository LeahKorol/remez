from django.db import transaction
from rest_framework import serializers

from analysis.models import DrugName, Query, ReactionName


class QuerySerializer(serializers.ModelSerializer):
    # Accepts only arrays of IDs for drugs and reactions on input (create/update)
    drugs = serializers.PrimaryKeyRelatedField(
        many=True, queryset=DrugName.objects.all()
    )
    reactions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ReactionName.objects.all()
    )

    def to_representation(self, instance):
        # On output (GET, PUT, POST), returns arrays of objects with both id and name for drugs and reactions
        # This overrides the default representation provided by PrimaryKeyRelatedField
        # It allows showing the drugs and reations names to the user without needing extra requests
        rep = super().to_representation(instance)
        rep["drugs"] = [
            {"id": drug.id, "name": drug.name} for drug in instance.drugs.all()
        ]
        rep["reactions"] = [
            {"id": reaction.id, "name": reaction.name}
            for reaction in instance.reactions.all()
        ]
        return rep

    class Meta:
        model = Query
        fields = "__all__"

        read_only_fields = (
            "id",
            "user",
            "created_at",
            "updated_at",
            "ror_values",
            "ror_lower",
            "ror_upper",
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
        This method handles the atomic creation of a Query object along with its
        many-to-many relationships with drugs and reactions.
        """
        drugs = validated_data.pop("drugs")
        reactions = validated_data.pop("reactions")
        with transaction.atomic():
            query = Query.objects.create(**validated_data)
            query.drugs.set(drugs)
            query.reactions.set(reactions)

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

        # Handle ROR fields that are read-only but can be updated by the system.
        # These values are recalculated when other fields change and injected via
        # the view's perform_update method.
        # Direct user modifications to read-only fields are ignored by DRF
        for field in ("ror_values", "ror_lower", "ror_upper", "updated_by"):
            if field in validated_data:
                setattr(instance, field, validated_data.pop(field))

        return super().update(instance, validated_data)


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
