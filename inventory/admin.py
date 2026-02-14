from django.contrib import admin
from django.utils.html import format_html
from .models import Car, Appointment, Favorite


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = (
        "display_image",
        "brand",
        "model",
        "year",
        "price",
        "kilometrage",
        "fuel",
        "status",
        "created_at",
    )
    search_fields = ("brand", "model", "city")
    list_filter = ("brand", "fuel", "transmission", "status", "city")
    list_editable = ("status",)
    list_per_page = 25

    def display_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height:auto; border-radius:5px;" />',
                obj.image.url,
            )
        return "Pas d'image"

    display_image.short_description = "Aperçu"


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("user", "car", "phone", "email", "date_rdv", "created_at")
    list_filter = ("date_rdv", "created_at")
    search_fields = ("user__username", "car__brand", "phone", "email")
    list_per_page = 25


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "car", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "car__brand")
