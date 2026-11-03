from django import forms

from .models import Car

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ["name", "color"]

    def clean_color(self):
        return self.cleaned_data["color"].lower()