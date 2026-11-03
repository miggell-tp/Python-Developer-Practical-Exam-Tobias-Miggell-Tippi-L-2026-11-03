from django import forms

from .models import Car

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ["name", "color"]

    def clean_color(self):
        return self.cleaned_data["color"].lower()
    
class CarMoveForm(forms.Form):
    before_id = forms.IntegerField(
        label="Move before car ID",
        required=False,
        min_value=1,
        max_value=2**63 - 1,
        help_text="Enter a car ID from the list, or leave this blank to move to the end.",
    )