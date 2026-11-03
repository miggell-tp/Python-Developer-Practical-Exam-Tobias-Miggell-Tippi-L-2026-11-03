from django.test import TestCase
from django.urls import reverse

from .models import Car
from .ordering import move_car

# Create your tests here.
class CarOrderingTests(TestCase):
    def setUp(self):
        self.first = Car.objects.create(name="Car D", color="blue", order_key=100)
        self.second = Car.objects.create(name="Car B", color="red", order_key=200)
        self.third = Car.objects.create(name="Car E", color="blue", order_key=300)

    def ordered_ids(self):
        return list(Car.objects.values_list("pk", flat=True))

    def test_move_to_front_changes_only_the_moved_key(self):
        self.assertTrue(move_car(self.third.pk, self.first.pk))

        self.assertEqual(self.ordered_ids(), [self.third.pk, self.first.pk, self.second.pk])
        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertEqual(self.first.order_key, 100)
        self.assertEqual(self.second.order_key, 200)

    def test_move_to_end(self):
        self.assertTrue(move_car(self.first.pk))

        self.assertEqual(self.ordered_ids(), [self.second.pk, self.third.pk, self.first.pk])

    def test_moving_before_self_or_current_successor_is_a_no_op(self):
        self.assertFalse(move_car(self.first.pk, self.first.pk))
        self.assertFalse(move_car(self.first.pk, self.second.pk))

        self.assertEqual(self.ordered_ids(), [self.first.pk, self.second.pk, self.third.pk])

    def test_missing_destination_preserves_order(self):
        with self.assertRaises(Car.DoesNotExist):
            move_car(self.first.pk, self.third.pk + 1)

        self.assertEqual(self.ordered_ids(), [self.first.pk, self.second.pk, self.third.pk])

    def test_adjacent_keys_are_rebalanced_before_inserting(self):
        Car.objects.filter(pk=self.second.pk).update(order_key=101)

        self.assertTrue(move_car(self.third.pk, self.second.pk))

        self.assertEqual(self.ordered_ids(), [self.first.pk, self.third.pk, self.second.pk])
        
class CarPageTests(TestCase):
    def setUp(self):
        self.car = Car.objects.create(name="Car D", color="blue", order_key=100)

    def test_add_car_normalizes_color_and_appends(self):
        response = self.client.post(
            reverse("cars:add"),
            {"name": "Car B", "color": " Red "},
        )

        self.assertRedirects(response, reverse("cars:list"))
        added_car = Car.objects.get(name="Car B")
        self.assertEqual(added_car.color, "red")
        self.assertGreater(added_car.order_key, self.car.order_key)

    def test_add_rejects_a_blank_name(self):
        response = self.client.post(
            reverse("cars:add"),
            {"name": "", "color": "blue"},
        )

        self.assertFormError(response.context["form"], "name", "This field is required.")
        self.assertEqual(Car.objects.count(), 1)

    def test_edit_preserves_order_key(self):
        response = self.client.post(
            reverse("cars:edit", args=[self.car.pk]),
            {"name": "Car D updated", "color": "green"},
        )

        self.assertRedirects(response, reverse("cars:list"))
        self.car.refresh_from_db()
        self.assertEqual(self.car.name, "Car D updated")
        self.assertEqual(self.car.color, "green")
        self.assertEqual(self.car.order_key, 100)

    def test_delete_requires_a_post(self):
        url = reverse("cars:delete", args=[self.car.pk])

        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Car.objects.filter(pk=self.car.pk).exists())

        self.assertRedirects(self.client.post(url), reverse("cars:list"))
        self.assertFalse(Car.objects.filter(pk=self.car.pk).exists())

    def test_color_filter_preserves_order_across_pages(self):
        Car.objects.create(name="Car B", color="red", order_key=150)
        blue_cars = [
            Car(name=f"Blue car {key}", color="blue", order_key=key)
            for key in range(126, 100, -1)
        ]
        Car.objects.bulk_create(blue_cars)
        url = reverse("cars:list")

        first_page = self.client.get(url, {"color": "Blue"})
        second_page = self.client.get(url, {"color": "Blue", "page": 2})

        first_keys = [car.order_key for car in first_page.context["cars"]]
        second_keys = [car.order_key for car in second_page.context["cars"]]
        self.assertEqual(first_keys, list(range(100, 125)))
        self.assertEqual(second_keys, [125, 126])

    def test_move_form_reports_a_missing_destination(self):
        url = reverse("cars:move", args=[self.car.pk])
        response = self.client.post(url, {"before_id": self.car.pk + 1})

        self.assertIn("before_id", response.context["form"].errors)
        self.car.refresh_from_db()
        self.assertEqual(self.car.order_key, 100)

    def test_editing_a_missing_car_returns_404(self):
        url = reverse("cars:edit", args=[self.car.pk + 1])

        self.assertEqual(self.client.get(url).status_code, 404)