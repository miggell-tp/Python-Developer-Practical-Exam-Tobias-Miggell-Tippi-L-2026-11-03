from django.db import models

# Create your models here.
class Car(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=30)
    order_key = models.BigIntegerField(unique=True, editable=False)

    class Meta:
        ordering = ["order_key"]
        indexes = [
            models.Index(fields=["color", "order_key"], name="car_color_order_idx"),
        ]

    def __str__(self):
        return self.name