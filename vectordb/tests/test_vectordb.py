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
    manager.add_text(1, "Sample text 1", {"field": "value"})
    manager.add_text(2, "Sample text 2", {"field": "value"})

    related_vectors = manager.search("Sample text", k=1)
    assert len(related_vectors) == 1
    assert related_vectors.first().object_id == "1"


@pytest.mark.django_db
def test_related_objects():
    from vectordb.models import SampleModel

    sample_instance1 = SampleModel.objects.create(text="Sample text 1")
    sample_instance2 = SampleModel.objects.create(text="Sample text 2")
    manager = Vector.objects
    manager.add_instance(sample_instance1)
    manager.add_instance(sample_instance2)

    related_vectors = manager.search(sample_instance1, k=1)
    assert len(related_vectors) == 1
    assert related_vectors.first().object_id == str(sample_instance2.pk)


@pytest.mark.django_db
def test_search():
    manager = Vector.objects
    manager.add_text(1, "Sample text 1", {"field": "value", "user": 1})
    manager.add_text(2, "Sample text 2", {"field": "value2", "user": 1})
    search_result = manager.search("Sample text", k=1)
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
