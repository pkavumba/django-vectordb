try:
    from rest_framework import filters, viewsets
except ImportError:
    raise ImportError("rest_framework is required for the api to work")

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Vector
from .serializers import VectorSerializer


class VectorViewSet(viewsets.ModelViewSet):
    queryset = Vector.objects.all()
    serializer_class = VectorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["text", "metadata"]
    search_fields = ["text", "metadata"]

    @action(detail=False, methods=["get"], url_path="search")
    def search_vectors(self, request):
        query = request.query_params.get("query", None)
        k = int(request.query_params.get("k", 10))

        if query is None:
            return Response({"error": "A query parameter is required."}, status=400)

        try:
            results = self.queryset.search(query, k=k)
            serializer = self.get_serializer(results, many=True)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
