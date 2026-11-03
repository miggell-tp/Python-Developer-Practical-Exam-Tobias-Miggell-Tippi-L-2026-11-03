from django.db import transaction
from django.db.models import F

from .models import Car


ORDER_STEP = 1_000_000
MAX_ORDER_KEY = 2**63 - 1


def _neighbor_keys(car_id, before_id):
    other_cars = Car.objects.exclude(pk=car_id)
    upper = None

    if before_id is not None:
        upper = other_cars.values_list("order_key", flat=True).get(pk=before_id)
        other_cars = other_cars.filter(order_key__lt=upper)

    lower = (
        other_cars.order_by("-order_key")
        .values_list("order_key", flat=True)
        .first()
    )
    return lower or 0, upper


def _rebalance():
    cars = list(Car.objects.only("order_key").order_by("order_key"))

    # Free the positive keys before assigning new ones under the unique constraint.
    Car.objects.update(order_key=-F("order_key"))

    for position, car in enumerate(cars, start=1):
        car.order_key = position * ORDER_STEP

    for start in range(0, len(cars), 500):
        Car.objects.bulk_update(cars[start:start + 500], ["order_key"])


@transaction.atomic
def move_car(car_id, before_id=None):
    """Move a car before another car, or to the end when before_id is None."""
    car = Car.objects.only("order_key").get(pk=car_id)
    if car_id == before_id:
        return False

    lower, upper = _neighbor_keys(car_id, before_id)

    if lower < car.order_key and (upper is None or car.order_key < upper):
        return False

    if (upper is not None and upper - lower <= 1) or (
        upper is None and lower > MAX_ORDER_KEY - ORDER_STEP
    ):
        _rebalance()
        lower, upper = _neighbor_keys(car_id, before_id)

    new_key = lower + ORDER_STEP if upper is None else (lower + upper) // 2
    car.order_key = new_key
    car.save(update_fields=["order_key"])
    return True