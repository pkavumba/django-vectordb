from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

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
            self.stderr.write(
                self.style.ERROR(f"Model {model_name} not found in app myapp")
            )
            return

        # Get all instances of the model
        instances = model.objects.all()

        # Get all instances of Vector with the same content_type
        content_type = ContentType.objects.get_for_model(model)
        vector_instances = Vector.objects.filter(content_type=content_type)
        have_been_deleted_qs = vector_instances.exclude(
            object_id__in=instances.values_list("pk", flat=True)
        )

        num_to_remove = have_been_deleted_qs.count()

        if num_to_remove > 0:
            # Remove instances in Vector that are not in the given model
            have_been_deleted_qs.delete()

        count_adds = 0
        count_updates = 0
        count_skips = 0
        # Add instances to Vector that are not already there
        for instance in instances:
            if Vector.objects.filter(
                content_type=content_type,
                object_id=instance.pk,
            ).exists():
                db_instance = Vector.objects.get(
                    content_type=content_type,
                    object_id=instance.pk,
                )
                if (
                    db_instance.text != instance.get_vectordb_text()
                    or db_instance.metadata != instance.get_vectordb_metadata()
                ):
                    db_instance.text = instance.get_vectordb_text()
                    db_instance.metadata = instance.get_vectordb_metadata()
                    db_instance.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Updated {instance} in Vector model because text/metadata changed"
                        )
                    )
                    count_updates += 1
                else:
                    self.stdout.write(
                        f"Skipping {instance} because it exists and hasn't changed"
                    )
                    count_skips += 1
            else:
                Vector.objects.add_instance(instance)
                self.stdout.write(
                    self.style.SUCCESS(f"Added {instance} to Vector model")
                )
                count_adds += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced Vector model with {model_name}. {count_adds} added, "
                f"{count_updates} updated, {count_skips} skipped,"
                f" {num_to_remove} removed."
            )
        )
