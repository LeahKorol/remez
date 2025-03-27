from rest_framework import serializers
from analysis.models import DrugList, ReactionList, Query
from django.db import transaction


class QuerySerializer(serializers.ModelSerializer):
    drugs = serializers.PrimaryKeyRelatedField(
        many=True, queryset=DrugList.objects.all()
    )
    reactions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=ReactionList.objects.all()
    )

    class Meta:
        model = Query
        fields = "__all__"

        read_only_fields = (
            "id",
            "user",
            "created_at",
            "updated_at",
            "x_values",
            "y_values",
        )

    def validate(self, data):
        """Ensure drugs & reactions are not empty lists when included in the request."""
        if "drugs" in data and not data["drugs"]:
            raise serializers.ValidationError(
                {"drugs": "At least one drug is required."}
            )
        if "reactions" in data and not data["reactions"]:
            raise serializers.ValidationError(
                {"reactions": "At least one reaction is required."}
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
        The method performs a partial update on the instance, allowing updates to the basic fields
        (name, quarter_start, quarter_end) as well as related drugs and reactions. If neither drugs
        nor reactions are provided, it falls back to the standard update behavior.

        Note:
            This method uses database transaction to ensure atomicity of the update operation
            when updating related fields (drugs and reactions).
        """
        drugs = validated_data.pop("drugs", None)
        reactions = validated_data.pop("reactions", None)

        if not drugs and not reactions:
            return super().update(instance, validated_data)

        with transaction.atomic():
            instance.name = validated_data.get("name", instance.name)
            instance.quarter_start = validated_data.get(
                "quarter_start", instance.quarter_start
            )
            instance.quarter_end = validated_data.get(
                "quarter_end", instance.quarter_end
            )
            if drugs:
                instance.drugs.set(drugs)
            if reactions:
                instance.reactions.set(reactions)
            instance.save()

            return instance
        return None
