import pytest

from vectordb import utils


def test_rrf():
    list1 = [
        {"id": 1, "title": "Post 1", "description": "First post"},
        {"id": 2, "title": "Post 2", "description": "Second post"},
        {"id": 3, "title": "Post 3", "description": "Third post"},
    ]
    list2 = [
        {"id": 2, "title": "Post 2", "description": "Second post"},
        {"id": 3, "title": "Post 3", "description": "Third post"},
        {"id": 4, "title": "Post 4", "description": "Fourth post"},
    ]
    list3 = [
        {"id": 3, "title": "Post 3", "description": "Third post"},
        {"id": 1, "title": "Post 1", "description": "First post"},
        {"id": 4, "title": "Post 4", "description": "Fourth post"},
        {"id": 5, "title": "Post 5", "description": "Fifth post"},
    ]

    expected_result = [
        {
            "rrf_score": (1 / 63 + 1 / 62 + 1 / 61),
            "id": 3,
            "title": "Post 3",
            "description": "Third post",
        },
        {
            "rrf_score": (1 / 61 + 1 / 62),
            "id": 1,
            "title": "Post 1",
            "description": "First post",
        },
        {
            "rrf_score": (1 / 62 + 1 / 61),
            "id": 2,
            "title": "Post 2",
            "description": "Second post",
        },
        {
            "rrf_score": (1 / 63 + 1 / 63),
            "id": 4,
            "title": "Post 4",
            "description": "Fourth post",
        },
        {
            "rrf_score": (1 / 64),
            "id": 5,
            "title": "Post 5",
            "description": "Fifth post",
        },
    ]

    result = utils.rrf(list1, list2, list3, k=60)

    # Use pytest.approx to compare floating-point numbers with default tolerance
    for res, exp in zip(result, expected_result):
        assert res["rrf_score"] == pytest.approx(exp["rrf_score"], rel=1e-8)
        assert res["id"] == exp["id"]
        assert res["title"] == exp["title"]
        assert res["description"] == exp["description"]
        assert res["title"] == exp["title"]
        assert res["description"] == exp["description"]
