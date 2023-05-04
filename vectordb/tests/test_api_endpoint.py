import pytest
import json
from rest_framework import status
from rest_framework.test import APIClient
from vectordb.models import Vector


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_create_vector(api_client):
    url = "/vectordb/"
    data = {
        "text": "test text",
        "metadata": {"key": "value"},
        "object_id": 100,
        "content_type": None,
    }
    response = api_client.post(url, data=data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert Vector.objects.count() == 1
    assert Vector.objects.first().text == "test text"


@pytest.mark.django_db
def test_search_vectors(api_client):
    # Create a few Vector instances here for testing purposes

    url = "/vectordb/search/"
    response = api_client.get(url, {"query": "example", "k": 5})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) <= 5


@pytest.mark.django_db
def test_search_vectors_no_query(api_client):
    url = "/vectordb/search/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.data
