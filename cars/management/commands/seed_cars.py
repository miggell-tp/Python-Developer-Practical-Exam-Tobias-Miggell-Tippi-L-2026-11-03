from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cars.models import Car
from cars.ordering import MAX_ORDER_KEY, ORDER_STEP


COLORS = ("blue", "red", "silver", "white", "black")
BATCH_SIZE = 1_000


class Command(BaseCommand):
    help = "Add sample cars until the inventory reaches the requested total."

    def add_arguments(self, parser):
        parser.add_argument("--total", type=int, default=100_000)

    @transaction.atomic
    def handle(self, *args, **options):
        total = options["total"]
        if total < 0:
            raise CommandError("--total must be zero or greater.")

        existing = Car.objects.count()
        to_add = max(0, total - existing)
        last_key = (
            Car.objects.order_by("-order_key")
            .values_list("order_key", flat=True)
            .first()
            or 0
        )

        if last_key + to_add * ORDER_STEP > MAX_ORDER_KEY:
            raise CommandError("There is too little room after the last order key.")

        for start in range(0, to_add, BATCH_SIZE):
            end = min(start + BATCH_SIZE, to_add)
            cars = [
                Car(
                    name=f"Sample car {existing + offset + 1:06d}",
                    color=COLORS[offset % len(COLORS)],
                    order_key=last_key + (offset + 1) * ORDER_STEP,
                )
                for offset in range(start, end)
            ]
            Car.objects.bulk_create(cars)

        self.stdout.write(
            self.style.SUCCESS(f"Added {to_add} cars. Inventory total: {existing + to_add}.")
        )