"""Validate the trip's input JSON without creating database records."""

import math

from rest_framework import serializers


class CycleHoursField(serializers.FloatField):
    """Hours must be numeric; JSON booleans are not one or zero working hours."""

    def to_internal_value(self, data):
        if isinstance(data, bool):
            self.fail("invalid")
        return super().to_internal_value(data)


class TripRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=200)
    pickup_location = serializers.CharField(max_length=200)
    dropoff_location = serializers.CharField(max_length=200)
    current_cycle_used = CycleHoursField(min_value=0, max_value=70)

    def validate_current_cycle_used(self, value):
        if not math.isfinite(value):
            raise serializers.ValidationError("Enter a finite number between 0 and 70.")
        return value
