from __future__ import annotations

try:
    from rest_framework import serializers
except ImportError:
    raise ImportError("rest_framework is required for the api to work")

from .models import Vector


class VectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vector
        fields = ["embedding", "text", "metadata", "object_id", "content_type"]
