from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Appointment, Car, Message


# Formulaire d'inscription
class InscriptionForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control rounded-3 py-3")


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["phone", "email", "date_rdv", "message"]
        widgets = {
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: 651 197 514"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "votre@email.com"}
            ),
            "date_rdv": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Votre message...",
                }
            ),
        }


class CarForm(forms.ModelForm):
    """Form for admin car CRUD."""

    class Meta:
        model = Car
        fields = [
            "brand",
            "model",
            "price",
            "year",
            "kilometrage",
            "fuel",
            "transmission",
            "city",
            "status",
            "description",
            "image",
        ]
        widgets = {
            "brand": forms.TextInput(attrs={"class": "form-control"}),
            "model": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "kilometrage": forms.NumberInput(attrs={"class": "form-control"}),
            "fuel": forms.Select(attrs={"class": "form-select"}),
            "transmission": forms.Select(attrs={"class": "form-select"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class MessageForm(forms.ModelForm):
    """Form for sending messages."""

    class Meta:
        model = Message
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Votre message...",
                }
            ),
        }
