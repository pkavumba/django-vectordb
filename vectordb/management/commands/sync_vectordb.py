from django.apps import apps
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from vectordb.models import Vector


class Command(BaseCommand):
    help = "Syncs Vector model with instances of a given model"

    def add_arguments(self, parser):
        parser.add_argument("app_name", help="Name of the Django app")
        parser.add_argument("model", help="Name of the Django model")

    def handle(self, *args, **options):
        app_name = options["app_name"]
        model_name = options["model"]

        try:
            model = apps.get_model(app_name, model_name)
        except LookupError:
            self.stderr.write(f"Model {model_name} not found in app myapp")
            return

        # Get all instances of the model
        instances = model.objects.all()

        # Get all instances of Vector with the same content_type
        content_type = ContentType.objects.get_for_model(model)
        vector_instances = Vector.objects.filter(content_type=content_type)

        # Remove instances in Vector that are not in the given model
        vector_instances.exclude(
            object_id__in=instances.values_list("pk", flat=True)
        ).delete()

        # Add instances to Vector that are not already there
        for instance in instances:
            if Vector.objects.filter(
                content_type=content_type,
                object_id=instance.pk,
            ).exists():
                self.stdout.write(f"Skipping {model_name} because it already exists")
            else:
                Vector.objects.add_instance(instance)
                self.stdout.write(f"Added {model_name} to Vector model")

        self.stdout.write(f"Synced Vector model with {model_name}")
