from django.urls import path
from . import views

urlpatterns = [
    # --- Public ---
    path("", views.home, name="home"),
    path("voiture/<int:pk>/", views.car_detail, name="car_detail"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("vip/", views.vip_cars, name="vip_cars"),
    path(
        "rendez-vous/<int:car_id>/", views.appointment_create, name="appointment_create"
    ),
    path("favorite/<int:car_id>/", views.toggle_favorite, name="toggle_favorite"),
    path("mes-favoris/", views.favorite_list, name="favorite_list"),
    # --- Comparateur ---
    path("comparer/", views.compare_cars, name="compare_cars"),
    path("comparer/ajouter/<int:car_id>/", views.add_to_compare, name="add_to_compare"),
    path(
        "comparer/retirer/<int:car_id>/",
        views.remove_from_compare,
        name="remove_from_compare",
    ),
    # --- Messagerie client ---
    path("message/<int:car_id>/", views.send_message, name="send_message"),
    path("mes-messages/", views.my_messages, name="my_messages"),
    path(
        "mes-messages/<int:user_id>/",
        views.conversation_detail,
        name="conversation_detail",
    ),
    # --- Panel Admin ---
    path("panel/", views.admin_dashboard, name="admin_dashboard"),
    path("panel/voitures/", views.admin_cars, name="admin_cars"),
    path("panel/voitures/ajouter/", views.admin_car_create, name="admin_car_create"),
    path(
        "panel/voitures/<int:pk>/modifier/", views.admin_car_edit, name="admin_car_edit"
    ),
    path(
        "panel/voitures/<int:pk>/supprimer/",
        views.admin_car_delete,
        name="admin_car_delete",
    ),
    path(
        "panel/voitures/<int:pk>/toggle/",
        views.admin_car_toggle,
        name="admin_car_toggle",
    ),
    path("panel/messages/", views.admin_messages, name="admin_messages"),
    path(
        "panel/messages/<int:user_id>/",
        views.admin_conversation,
        name="admin_conversation",
    ),
    path("panel/utilisateurs/", views.admin_users, name="admin_users"),
    path("panel/activite/", views.admin_activity, name="admin_activity"),
    path("panel/rendez-vous/", views.admin_appointments, name="admin_appointments"),
]
