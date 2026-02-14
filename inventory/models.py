from django.db import models
from django.contrib.auth.models import User


class Car(models.Model):
    CARBURANT_CHOICES = [
        ("Essence", "Essence"),
        ("Diesel", "Diesel"),
        ("Hybride", "Hybride"),
        ("Electrique", "Électrique"),
    ]
    BOITE_CHOICES = [
        ("Manuelle", "Manuelle"),
        ("Automatique", "Automatique"),
    ]
    STATUT_CHOICES = [
        ("Disponible", "Disponible"),
        ("Vendu", "Vendu"),
        ("En attente", "En attente de validation"),
    ]

    brand = models.CharField(max_length=100, verbose_name="Marque", db_index=True)
    model = models.CharField(max_length=100, verbose_name="Modèle")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Prix", db_index=True
    )
    year = models.IntegerField(verbose_name="Année", db_index=True)
    kilometrage = models.IntegerField(default=0, verbose_name="Kilométrage")
    fuel = models.CharField(
        max_length=20,
        choices=CARBURANT_CHOICES,
        default="Essence",
        verbose_name="Carburant",
        db_index=True,
    )
    transmission = models.CharField(
        max_length=20,
        choices=BOITE_CHOICES,
        default="Manuelle",
        verbose_name="Boîte de vitesse",
    )
    city = models.CharField(
        max_length=100, default="Yaoundé", verbose_name="Ville", db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="En attente",
        verbose_name="Statut",
        db_index=True,
    )
    description = models.TextField(blank=True, verbose_name="Description")
    image = models.ImageField(
        upload_to="cars/", blank=True, null=True, verbose_name="Photo principale"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "price"], name="idx_status_price"),
            models.Index(fields=["status", "-created_at"], name="idx_status_created"),
        ]

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year}) - {self.price} FCFA"


class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    email = models.EmailField(verbose_name="Email")
    date_rdv = models.DateTimeField(verbose_name="Date et Heure")
    message = models.TextField(blank=True, verbose_name="Message")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_rdv"]

    def __str__(self):
        return f"RDV de {self.user.username} pour {self.car.brand}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "car")

    def __str__(self):
        return f"{self.user.username} ♥ {self.car.brand} {self.car.model}"


class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    car = models.ForeignKey(
        Car, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages"
    )
    content = models.TextField(verbose_name="Message")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["receiver", "is_read"], name="idx_msg_receiver_read"),
        ]

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.content[:40]}"


class SiteVisit(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True, default="Inconnu")
    city = models.CharField(max_length=100, blank=True, default="Inconnu")
    page = models.CharField(max_length=500, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"], name="idx_visit_created"),
        ]

    def __str__(self):
        return f"{self.ip_address} — {self.page} — {self.created_at:%d/%m %H:%M}"
