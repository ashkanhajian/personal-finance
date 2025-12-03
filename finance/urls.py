from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
]