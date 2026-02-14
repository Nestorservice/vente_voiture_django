from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Car, Favorite, Appointment, Message, SiteVisit
from .forms import InscriptionForm, AppointmentForm, CarForm, MessageForm


# ═══════════════════════════════════════════
# PAGES PUBLIQUES
# ═══════════════════════════════════════════


# --- ACCUEIL + FILTRES AVANCÉS ---
def home(request):
    cars = Car.objects.filter(status="Disponible").only(
        "id",
        "brand",
        "model",
        "price",
        "year",
        "kilometrage",
        "fuel",
        "city",
        "image",
        "description",
        "status",
        "created_at",
    )

    # Recherche texte
    query = request.GET.get("q", "")
    if query:
        cars = cars.filter(
            Q(brand__icontains=query)
            | Q(model__icontains=query)
            | Q(city__icontains=query)
        )

    # Filtres avancés
    fuel = request.GET.get("fuel", "")
    transmission = request.GET.get("transmission", "")
    price_min = request.GET.get("price_min", "")
    price_max = request.GET.get("price_max", "")
    year_min = request.GET.get("year_min", "")
    year_max = request.GET.get("year_max", "")
    city = request.GET.get("city", "")

    if fuel:
        cars = cars.filter(fuel=fuel)
    if transmission:
        cars = cars.filter(transmission=transmission)
    if price_min:
        cars = cars.filter(price__gte=price_min)
    if price_max:
        cars = cars.filter(price__lte=price_max)
    if year_min:
        cars = cars.filter(year__gte=year_min)
    if year_max:
        cars = cars.filter(year__lte=year_max)
    if city:
        cars = cars.filter(city__icontains=city)

    cars = cars.order_by("-created_at")

    # Pagination
    paginator = Paginator(cars, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Favoris de l'utilisateur
    user_favorites = []
    if request.user.is_authenticated:
        user_favorites = list(
            Favorite.objects.filter(user=request.user).values_list("car_id", flat=True)
        )

    # Données pour les filtres
    available_cities = (
        Car.objects.filter(status="Disponible")
        .values_list("city", flat=True)
        .distinct()
        .order_by("city")
    )

    return render(
        request,
        "inventory/home.html",
        {
            "cars": page_obj,
            "page_obj": page_obj,
            "year": datetime.now().year,
            "query": query,
            "user_favorites": user_favorites,
            "fuel": fuel,
            "transmission": transmission,
            "price_min": price_min,
            "price_max": price_max,
            "year_min": year_min,
            "year_max": year_max,
            "selected_city": city,
            "available_cities": available_cities,
            "fuel_choices": Car.CARBURANT_CHOICES,
            "transmission_choices": Car.BOITE_CHOICES,
            "total_results": paginator.count,
        },
    )


# --- GESTION DES FAVORIS ---
@login_required
def toggle_favorite(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, car=car)

    if not created:
        favorite.delete()
        messages.info(request, f"{car.brand} retirée des favoris.")
    else:
        messages.success(request, f"{car.brand} ajoutée aux favoris !")

    return redirect(request.META.get("HTTP_REFERER", "home"))


# --- PAGE DES FAVORIS ---
@login_required
def favorite_list(request):
    my_favorites = Favorite.objects.filter(user=request.user).select_related("car")
    return render(
        request,
        "inventory/favorites.html",
        {"favorites": my_favorites, "year": datetime.now().year},
    )


# --- DÉTAILS VOITURE ---
def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    similar_cars = (
        Car.objects.filter(brand=car.brand, status="Disponible")
        .exclude(pk=pk)
        .only("id", "brand", "model", "price", "image")[:3]
    )

    # Message form for authenticated users
    message_form = MessageForm() if request.user.is_authenticated else None

    return render(
        request,
        "inventory/car_detail.html",
        {
            "car": car,
            "similar_cars": similar_cars,
            "year": datetime.now().year,
            "message_form": message_form,
        },
    )


# --- INSCRIPTION ---
def register_view(request):
    if request.method == "POST":
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Compte créé ! Vous êtes connecté.")
            return redirect("home")
    else:
        form = InscriptionForm()
    return render(request, "inventory/register.html", {"form": form})


# --- CONNEXION ---
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenue, {username} !")
                next_url = request.GET.get("next", "home")
                return redirect(next_url)
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = AuthenticationForm()
    return render(request, "inventory/login.html", {"form": form})


# --- DÉCONNEXION ---
def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect("home")


# --- RENDEZ-VOUS ---
@login_required
def appointment_create(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.user = request.user
            appointment.car = car
            appointment.save()
            messages.success(request, "Votre demande de rendez-vous a été envoyée !")
            return redirect("car_detail", pk=car.id)
    else:
        form = AppointmentForm()
    return render(
        request, "inventory/appointment_form.html", {"form": form, "car": car}
    )


# --- SECTION VIP ---
@login_required
def vip_cars(request):
    cars_vip = Car.objects.filter(price__gte=20000000, status="Disponible").order_by(
        "-price"
    )
    return render(
        request,
        "inventory/vip_cars.html",
        {"cars": cars_vip, "year": datetime.now().year},
    )


# --- COMPARATEUR DE VÉHICULES ---
@login_required
def add_to_compare(request, car_id):
    compare_list = request.session.get("compare_list", [])
    if car_id not in compare_list:
        if len(compare_list) >= 2:
            compare_list.pop(0)
        compare_list.append(car_id)
        request.session["compare_list"] = compare_list
        messages.success(request, "Véhicule ajouté au comparateur !")
    else:
        messages.info(request, "Ce véhicule est déjà dans le comparateur.")
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def remove_from_compare(request, car_id):
    compare_list = request.session.get("compare_list", [])
    if car_id in compare_list:
        compare_list.remove(car_id)
        request.session["compare_list"] = compare_list
        messages.info(request, "Véhicule retiré du comparateur.")
    return redirect("compare_cars")


@login_required
def compare_cars(request):
    compare_list = request.session.get("compare_list", [])
    cars = Car.objects.filter(id__in=compare_list)
    all_cars = Car.objects.filter(status="Disponible").order_by("brand", "model")
    return render(
        request,
        "inventory/compare.html",
        {"cars": cars, "all_cars": all_cars, "year": datetime.now().year},
    )


# --- MESSAGERIE CLIENT ---
@login_required
def send_message(request, car_id):
    """Client sends a message about a car to admin."""
    car = get_object_or_404(Car, id=car_id)
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            # Send to the first superuser/staff
            admin_user = User.objects.filter(is_staff=True).first()
            if admin_user:
                msg = form.save(commit=False)
                msg.sender = request.user
                msg.receiver = admin_user
                msg.car = car
                msg.save()
                messages.success(request, "Message envoyé avec succès !")
            else:
                messages.error(request, "Aucun administrateur disponible.")
        return redirect("car_detail", pk=car.id)
    return redirect("car_detail", pk=car.id)


@login_required
def my_messages(request):
    """Client sees their conversations."""
    # Get all messages where user is sender or receiver
    user_messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).select_related("sender", "receiver", "car")

    # Group by conversation partner
    conversations = {}
    for msg in user_messages:
        partner = msg.receiver if msg.sender == request.user else msg.sender
        key = partner.id
        if key not in conversations:
            conversations[key] = {
                "partner": partner,
                "car": msg.car,
                "last_message": msg,
                "unread": 0,
            }
        conversations[key]["last_message"] = msg
        if msg.receiver == request.user and not msg.is_read:
            conversations[key]["unread"] += 1

    return render(
        request,
        "inventory/my_messages.html",
        {"conversations": conversations.values(), "year": datetime.now().year},
    )


@login_required
def conversation_detail(request, user_id):
    """View a specific conversation."""
    partner = get_object_or_404(User, id=user_id)

    conv_messages = Message.objects.filter(
        (Q(sender=request.user, receiver=partner))
        | (Q(sender=partner, receiver=request.user))
    ).select_related("sender", "receiver", "car")

    # Mark as read
    conv_messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = partner
            # Use the car from the last message in thread
            last_car_msg = conv_messages.filter(car__isnull=False).last()
            if last_car_msg:
                msg.car = last_car_msg.car
            msg.save()
            messages.success(request, "Message envoyé !")
            return redirect("conversation_detail", user_id=user_id)
    else:
        form = MessageForm()

    return render(
        request,
        "inventory/conversation.html",
        {
            "partner": partner,
            "messages_list": conv_messages,
            "form": form,
            "year": datetime.now().year,
        },
    )


# ═══════════════════════════════════════════
# PANEL ADMIN PERSONNALISÉ
# ═══════════════════════════════════════════


@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard with stats and chart data."""
    now = timezone.now()
    last_30 = now - timedelta(days=30)
    last_7 = now - timedelta(days=7)

    # Stats
    total_cars = Car.objects.count()
    available_cars = Car.objects.filter(status="Disponible").count()
    sold_cars = Car.objects.filter(status="Vendu").count()
    pending_cars = Car.objects.filter(status="En attente").count()
    total_users = User.objects.filter(is_staff=False).count()
    total_appointments = Appointment.objects.count()
    recent_appointments = Appointment.objects.filter(created_at__gte=last_7).count()
    total_messages = Message.objects.count()
    unread_messages = Message.objects.filter(
        receiver__is_staff=True, is_read=False
    ).count()
    total_visits = SiteVisit.objects.filter(created_at__gte=last_30).count()
    today_visits = SiteVisit.objects.filter(created_at__date=now.date()).count()

    # Revenue estimate (sold cars)
    revenue = (
        Car.objects.filter(status="Vendu").aggregate(total=Sum("price"))["total"] or 0
    )

    # Chart: Cars by status
    cars_by_status = {
        "Disponible": available_cars,
        "Vendu": sold_cars,
        "En attente": pending_cars,
    }

    # Chart: Visits per day (last 7 days)
    visits_per_day = (
        SiteVisit.objects.filter(created_at__gte=last_7)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    visit_labels = [v["day"].strftime("%d/%m") for v in visits_per_day]
    visit_data = [v["count"] for v in visits_per_day]

    # Chart: Appointments per month (last 6 months)
    six_months_ago = now - timedelta(days=180)
    rdv_per_month = (
        Appointment.objects.filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    rdv_labels = [r["month"].strftime("%b %Y") for r in rdv_per_month]
    rdv_data = [r["count"] for r in rdv_per_month]

    # Recent activity
    recent_cars = Car.objects.order_by("-created_at")[:5]
    recent_rdvs = Appointment.objects.order_by("-created_at")[:5]
    recent_msgs = Message.objects.filter(receiver__is_staff=True).order_by(
        "-created_at"
    )[:5]

    # Online users (visited in last 5 minutes)
    five_min_ago = now - timedelta(minutes=5)
    online_count = (
        SiteVisit.objects.filter(created_at__gte=five_min_ago)
        .values("ip_address")
        .distinct()
        .count()
    )

    return render(
        request,
        "inventory/admin/dashboard.html",
        {
            "total_cars": total_cars,
            "available_cars": available_cars,
            "sold_cars": sold_cars,
            "pending_cars": pending_cars,
            "total_users": total_users,
            "total_appointments": total_appointments,
            "recent_appointments": recent_appointments,
            "total_messages": total_messages,
            "unread_messages": unread_messages,
            "total_visits": total_visits,
            "today_visits": today_visits,
            "revenue": revenue,
            "online_count": online_count,
            # Charts
            "cars_by_status": cars_by_status,
            "visit_labels": visit_labels,
            "visit_data": visit_data,
            "rdv_labels": rdv_labels,
            "rdv_data": rdv_data,
            # Recent
            "recent_cars": recent_cars,
            "recent_rdvs": recent_rdvs,
            "recent_msgs": recent_msgs,
        },
    )


@staff_member_required
def admin_cars(request):
    """Car management with search and filter."""
    cars = Car.objects.all()
    q = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")

    if q:
        cars = cars.filter(
            Q(brand__icontains=q) | Q(model__icontains=q) | Q(city__icontains=q)
        )
    if status_filter:
        cars = cars.filter(status=status_filter)

    cars = cars.order_by("-created_at")
    paginator = Paginator(cars, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "inventory/admin/admin_cars.html",
        {
            "cars": page_obj,
            "page_obj": page_obj,
            "q": q,
            "status_filter": status_filter,
            "statut_choices": Car.STATUT_CHOICES,
        },
    )


@staff_member_required
def admin_car_create(request):
    """Create a new car."""
    if request.method == "POST":
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Véhicule ajouté avec succès !")
            return redirect("admin_cars")
    else:
        form = CarForm()
    return render(
        request,
        "inventory/admin/admin_car_form.html",
        {"form": form, "title": "Ajouter un véhicule"},
    )


@staff_member_required
def admin_car_edit(request, pk):
    """Edit an existing car."""
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, "Véhicule modifié avec succès !")
            return redirect("admin_cars")
    else:
        form = CarForm(instance=car)
    return render(
        request,
        "inventory/admin/admin_car_form.html",
        {"form": form, "car": car, "title": f"Modifier {car.brand} {car.model}"},
    )


@staff_member_required
def admin_car_delete(request, pk):
    """Delete a car."""
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        car.delete()
        messages.success(request, "Véhicule supprimé.")
        return redirect("admin_cars")
    return render(
        request,
        "inventory/admin/admin_car_confirm_delete.html",
        {"car": car},
    )


@staff_member_required
def admin_car_toggle(request, pk):
    """Toggle car status between Disponible/Vendu."""
    car = get_object_or_404(Car, pk=pk)
    if car.status == "Disponible":
        car.status = "Vendu"
    elif car.status == "Vendu":
        car.status = "Disponible"
    elif car.status == "En attente":
        car.status = "Disponible"
    car.save()
    messages.success(request, f"{car.brand} {car.model} → {car.status}")
    return redirect("admin_cars")


@staff_member_required
def admin_messages(request):
    """Admin inbox — grouped by sender."""
    all_msgs = Message.objects.filter(
        Q(receiver__is_staff=True) | Q(sender__is_staff=True)
    ).select_related("sender", "receiver", "car")

    conversations = {}
    for msg in all_msgs:
        # The client is the non-staff user
        client = msg.sender if not msg.sender.is_staff else msg.receiver
        key = client.id
        if key not in conversations:
            conversations[key] = {
                "client": client,
                "car": msg.car,
                "last_message": msg,
                "unread": 0,
                "total": 0,
            }
        conversations[key]["last_message"] = msg
        conversations[key]["total"] += 1
        if msg.receiver.is_staff and not msg.is_read:
            conversations[key]["unread"] += 1

    return render(
        request,
        "inventory/admin/admin_messages.html",
        {"conversations": conversations.values()},
    )


@staff_member_required
def admin_conversation(request, user_id):
    """Admin views/responds to a client conversation."""
    client = get_object_or_404(User, id=user_id)

    conv_messages = Message.objects.filter(
        (Q(sender=client, receiver__is_staff=True))
        | (Q(sender__is_staff=True, receiver=client))
    ).select_related("sender", "receiver", "car")

    # Mark as read
    conv_messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.receiver = client
            last_car_msg = conv_messages.filter(car__isnull=False).last()
            if last_car_msg:
                msg.car = last_car_msg.car
            msg.save()
            messages.success(request, "Réponse envoyée !")
            return redirect("admin_conversation", user_id=user_id)
    else:
        form = MessageForm()

    return render(
        request,
        "inventory/admin/admin_conversation.html",
        {"client": client, "messages_list": conv_messages, "form": form},
    )


@staff_member_required
def admin_users(request):
    """User management / list."""
    users = (
        User.objects.filter(is_staff=False)
        .annotate(
            fav_count=Count("favorite"),
            msg_count=Count("sent_messages"),
        )
        .order_by("-date_joined")
    )

    q = request.GET.get("q", "")
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q))

    paginator = Paginator(users, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "inventory/admin/admin_users.html",
        {"users": page_obj, "page_obj": page_obj, "q": q},
    )


@staff_member_required
def admin_activity(request):
    """Site visit / activity log."""
    visits = SiteVisit.objects.select_related("user").order_by("-created_at")

    q = request.GET.get("q", "")
    if q:
        visits = visits.filter(
            Q(ip_address__icontains=q)
            | Q(page__icontains=q)
            | Q(user__username__icontains=q)
        )

    paginator = Paginator(visits, 30)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Unique IPs today
    today = timezone.now().date()
    unique_ips_today = (
        SiteVisit.objects.filter(created_at__date=today)
        .values("ip_address")
        .distinct()
        .count()
    )

    return render(
        request,
        "inventory/admin/admin_activity.html",
        {
            "visits": page_obj,
            "page_obj": page_obj,
            "q": q,
            "unique_ips_today": unique_ips_today,
        },
    )


@staff_member_required
def admin_appointments(request):
    """Admin view for all appointments with details."""
    now = timezone.now()
    appointments = Appointment.objects.select_related("user", "car").order_by(
        "-created_at"
    )

    q = request.GET.get("q", "")
    if q:
        appointments = appointments.filter(
            Q(user__username__icontains=q)
            | Q(car__brand__icontains=q)
            | Q(car__model__icontains=q)
            | Q(phone__icontains=q)
            | Q(email__icontains=q)
        )

    status_filter = request.GET.get("status", "")
    if status_filter == "upcoming":
        appointments = appointments.filter(date_rdv__gte=now)
    elif status_filter == "past":
        appointments = appointments.filter(date_rdv__lt=now)

    paginator = Paginator(appointments, 15)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Stats
    total_rdv = Appointment.objects.count()
    upcoming_rdv = Appointment.objects.filter(date_rdv__gte=now).count()
    past_rdv = Appointment.objects.filter(date_rdv__lt=now).count()
    this_week = Appointment.objects.filter(
        created_at__gte=now - timedelta(days=7)
    ).count()

    return render(
        request,
        "inventory/admin/admin_appointments.html",
        {
            "appointments": page_obj,
            "page_obj": page_obj,
            "q": q,
            "status_filter": status_filter,
            "total_rdv": total_rdv,
            "upcoming_rdv": upcoming_rdv,
            "past_rdv": past_rdv,
            "this_week": this_week,
        },
    )
