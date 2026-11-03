from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CarForm
from .models import Car

# Create your views here.

ORDER_STEP = 1_000_000


class CarListView(ListView):
    model = Car
    template_name = "cars/car_list.html"
    context_object_name = "cars"


class CarCreateView(CreateView):
    model = Car
    form_class = CarForm
    template_name = "cars/car_form.html"
    success_url = reverse_lazy("cars:list")

    @transaction.atomic
    def form_valid(self, form):
        last_key = (
            Car.objects.order_by("-order_key")
            .values_list("order_key", flat=True)
            .first()
        )
        form.instance.order_key = (last_key or 0) + ORDER_STEP
        return super().form_valid(form)


class CarUpdateView(UpdateView):
    model = Car
    form_class = CarForm
    template_name = "cars/car_form.html"
    success_url = reverse_lazy("cars:list")


class CarDeleteView(DeleteView):
    model = Car
    template_name = "cars/car_confirm_delete.html"
    success_url = reverse_lazy("cars:list")