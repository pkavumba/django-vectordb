from django.apps import apps  # noqa F401
from django.core.management.base import BaseCommand

from vectordb.models import Vector


class Command(BaseCommand):
    help = "Reset the vector database"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "The operation is not revisable. It will delete all the vectors in the database."
            )
        )
        # Ask the user for confirmation
        user_input = input("Do you want to continue with the reset? (yes/no): ")

        # Check if the user wants to continue
        if user_input.lower() == "yes":
            self.stdout.write(self.style.SUCCESS("Resetting the vector database..."))
            Vector.objects.all.delete()
            if Vector.objects.index:
                Vector.objects.index.reset()
        else:
            self.stdout.write(self.style.WARNING("Reset was canceled."))
