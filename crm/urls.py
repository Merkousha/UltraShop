from django.urls import path
from crm import views

app_name = "crm"

urlpatterns = [
    path("", views.CRMDashboardView.as_view(), name="dashboard"),
    path("leads/", views.LeadKanbanView.as_view(), name="lead-kanban"),
    path("leads/create/", views.LeadCreateView.as_view(), name="lead-create"),
    path("leads/<int:pk>/", views.LeadDetailView.as_view(), name="lead-detail"),
    path("leads/<int:pk>/stage/", views.LeadUpdateStageView.as_view(), name="lead-update-stage"),
    path("tasks/", views.TaskListView.as_view(), name="task-list"),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task-create"),
    path("tasks/<int:pk>/toggle/", views.TaskToggleDoneView.as_view(), name="task-toggle"),
    path("contacts/", views.ContactHistoryView.as_view(), name="contact-history"),
]
