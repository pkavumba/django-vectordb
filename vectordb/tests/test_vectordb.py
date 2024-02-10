import pytest
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError

from vectordb.models import Vector


@pytest.mark.django_db
def test_add_text():
    manager = Vector.objects
    vector = manager.add_text(1, "Sample text", {"field": "value"})

    assert vector.object_id == 1
    assert vector.text == "Sample text"
    assert vector.metadata == {"field": "value"}
    assert vector.vector.shape == (384,)


@pytest.mark.django_db
def test_add_instance():
    from vectordb.models import SampleModel

    sample_instance = SampleModel.objects.create(text="Sample text")
    manager = Vector.objects
    vector = manager.add_instance(sample_instance)
    content_type = ContentType.objects.get_for_model(SampleModel)

    assert vector.object_id == sample_instance.pk
    assert vector.text == "Sample text"
    assert vector.content_type == content_type
    assert vector.vector.shape == (384,)


@pytest.mark.django_db
def test_add_text_with_same_id_errors():
    manager = Vector.objects
    manager.add_text(1, "Sample text", {"field": "value"})
    with pytest.raises(IntegrityError):
        manager.add_text(1, "Sample text", {"field": "value"})


@pytest.mark.django_db
def test_add__same_sample_object_errors():
    from vectordb.models import SampleModel

    sample_instance = SampleModel.objects.create(text="Sample text")
    manager = Vector.objects
    manager.add_instance(sample_instance)
    with pytest.raises(IntegrityError):
        manager.add_instance(sample_instance)


@pytest.mark.django_db
def test_related_texts():
    manager = Vector.objects
    manager.add_text(1, "The green fox jumps 1", {"field": "value"})
    manager.add_text(2, "The person walks", {"field": "value"})
    manager.add_text(3, "The person in a blue shirt smiles", {"field": "value"})

    related_vectors = manager.search("fox jumps", k=1)
    assert len(related_vectors) == 1
    assert related_vectors.first().object_id == "1"


@pytest.mark.django_db
def test_related_objects():
    from vectordb.models import SampleModel

    sample_instance1 = SampleModel.objects.create(text="The green fox jumps 1")
    sample_instance2 = SampleModel.objects.create(text="The green fox jumps 2")
    sample_instance3 = SampleModel.objects.create(text="The person walks")
    manager = Vector.objects
    manager.add_instance(sample_instance1)
    manager.add_instance(sample_instance2)
    manager.add_instance(sample_instance3)

    related_vectors = manager.search(sample_instance1, k=1)
    assert len(related_vectors) == 1
    assert related_vectors.first().object_id == str(sample_instance2.pk)


@pytest.mark.django_db
def test_search():
    manager = Vector.objects
    manager.add_text(1, "The green fox jumps 1", {"field": "value", "user": 1})
    manager.add_text(2, "The person walks", {"field": "value2", "user": 1})
    search_result = manager.search("green fox", k=1)
    assert len(search_result) == 1
    assert search_result.first().object_id == "1"


@pytest.mark.django_db
def test_search_filtering():
    manager = Vector.objects
    for idx in range(1, 20):
        manager.add_text(idx, f"Sample text {idx}", {"field": "value", "user": 1})

    for idx in range(20, 50):
        manager.add_text(idx, f"Sample text {idx}", {"field": "value", "user": 2})

    search_results = manager.filter(metadata__user=2).search("Sample text", k=10)
    assert len(search_results) == 10

    for match in search_results:
        print(match.metadata)
        assert match.metadata["user"] == 2


@pytest.mark.django_db
def test_search_unwrap_arg():
    manager = Vector.objects
    from vectordb.models import SampleModel

    manager = Vector.objects

    sample_instance1 = SampleModel.objects.create(text="The green fox jumps 1")
    sample_instance2 = SampleModel.objects.create(text="The green fox jumps 2")
    sample_instance3 = SampleModel.objects.create(text="The person walks")
    manager = Vector.objects
    manager.add_instance(sample_instance1)
    manager.add_instance(sample_instance2)
    manager.add_instance(sample_instance3)

    for idx in range(100, 130):
        manager.add_text(
            idx, f"The green fox jumps {idx}", {"field": "value", "user": 100}
        )

    search_results = manager.search("The green fox", k=20, unwrap=True)
    assert (
        len(search_results) == 2
    )  # will only match the first two objects, unwrap drops no Model instances
    assert isinstance(search_results, list)
    assert isinstance(search_results[0], SampleModel)


@pytest.mark.django_db
def test_search_unwrap_queryset():
    manager = Vector.objects
    from vectordb.models import SampleModel

    manager = Vector.objects

    sample_instance1 = SampleModel.objects.create(text="The green fox jumps 1")
    sample_instance2 = SampleModel.objects.create(text="The green fox jumps 2")
    sample_instance3 = SampleModel.objects.create(text="The person walks")
    manager = Vector.objects
    manager.add_instance(sample_instance1)
    manager.add_instance(sample_instance2)
    manager.add_instance(sample_instance3)

    for idx in range(100, 130):
        manager.add_text(
            idx, f"The green fox jumps {idx}", {"field": "value", "user": 100}
        )

    search_results = manager.search("The green fox", k=20).unwrap()
    assert (
        len(search_results) == 2
    )  # will only match the first two objects, unwrap drops no Model instances
    assert isinstance(search_results, list)
    assert isinstance(search_results[0], SampleModel)


@pytest.mark.django_db
def test_search_with_content_type_filter():
    from vectordb.models import SampleModel

    manager = Vector.objects

    sample_instance1 = SampleModel.objects.create(text="The green fox jumps 1")
    sample_instance2 = SampleModel.objects.create(text="The green fox jumps 2")
    manager = Vector.objects
    manager.add_instance(sample_instance1)
    manager.add_instance(sample_instance2)

    for idx in range(100, 130):
        manager.add_text(
            idx, f"The green fox jumps {idx}", {"field": "value", "user": 100}
        )

    search_results = manager.search("green fox jumps", k=20, content_type=SampleModel)

    assert len(search_results) == 2  # no text matches, only object matches
    for match in search_results:
        assert (
            "user" not in match.metadata
        )  # user metadata is only set in the add_text calls
