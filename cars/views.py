from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView

from django.contrib import messages
from django.shortcuts import get_object_or_404

from .forms import CarForm, CarMoveForm
from .models import Car
from .ordering import move_car

# Create your views here.

ORDER_STEP = 1_000_000


class CarListView(ListView):
    model = Car
    template_name = "cars/car_list.html"
    context_object_name = "cars"
    paginate_by = 25

    def get_queryset(self):
        cars = super().get_queryset()
        color = self.request.GET.get("color", "").strip().lower()

        if color:
            cars = cars.filter(color=color)

        return cars
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_color = self.request.GET.get("color", "").strip().lower()

        context["selected_color"] = selected_color
        context["quick_filters"] = [
            {
                "label": label,
                "value": color,
                "count": Car.objects.filter(color=color).count(),
            }
            for label, color in (
                ("Blue", "blue"),
                ("Red", "red"),
                ("Silver", "silver"),
            )
        ]
        return context

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
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CarDeleteView(DeleteView):
    model = Car
    template_name = "cars/car_confirm_delete.html"
    success_url = reverse_lazy("cars:list")
    
class CarMoveView(FormView):
    form_class = CarMoveForm
    template_name = "cars/car_move.html"
    success_url = reverse_lazy("cars:list")

    def dispatch(self, request, *args, **kwargs):
        self.car = get_object_or_404(Car, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super().get_context_data(car=self.car, **kwargs)

    def form_valid(self, form):
        try:
            moved = move_car(self.car.pk, form.cleaned_data["before_id"])
        except Car.DoesNotExist:
            form.add_error("before_id", "The car to move or the destination car no longer exists.")
            return self.form_invalid(form)

        if moved:
            messages.success(self.request, f"Moved {self.car.name}.")
        else:
            messages.info(self.request, f"{self.car.name} stayed in the same position.")

        return super().form_valid(form)