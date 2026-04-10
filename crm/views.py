from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from crm.models import ContactActivity, Lead, SaleTask
from customers.models import Customer
from dashboard.views import StoreAccessMixin


# ─── CRM Dashboard ────────────────────────────────────────
class CRMDashboardView(StoreAccessMixin, TemplateView):
    template_name = "crm/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        store = self.request.current_store
        today = timezone.localdate()

        # Leads by stage counts
        stage_counts = {}
        for stage in Lead.Stage.values:
            stage_counts[stage] = Lead.objects.filter(store=store, stage=stage).count()
        ctx["stage_counts"] = stage_counts
        ctx["total_leads"] = Lead.objects.filter(store=store).count()
        ctx["won_leads"] = stage_counts.get("won", 0)
        ctx["lost_leads"] = stage_counts.get("lost", 0)

        # Today's tasks
        ctx["todays_tasks"] = SaleTask.objects.filter(
            store=store, due_date=today, is_done=False
        ).select_related("lead")[:10]
        ctx["overdue_tasks"] = SaleTask.objects.filter(
            store=store, due_date__lt=today, is_done=False
        ).count()
        ctx["pending_tasks"] = SaleTask.objects.filter(
            store=store, is_done=False
        ).count()
        ctx["stage_choices"] = Lead.Stage.choices
        return ctx


# ─── Lead Kanban ─────────────────────────────────────────
class LeadKanbanView(StoreAccessMixin, TemplateView):
    template_name = "crm/lead_kanban.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        store = self.request.current_store
        columns = []
        for stage_value, stage_label in Lead.Stage.choices:
            leads = Lead.objects.filter(store=store, stage=stage_value).select_related("assigned_to")[:50]
            columns.append({
                "stage": stage_value,
                "label": stage_label,
                "leads": leads,
                "count": Lead.objects.filter(store=store, stage=stage_value).count(),
            })
        ctx["columns"] = columns
        ctx["stage_choices"] = Lead.Stage.choices
        return ctx


# ─── Lead Create ──────────────────────────────────────────
class LeadCreateView(StoreAccessMixin, TemplateView):
    template_name = "crm/lead_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["lead"] = None
        ctx["stage_choices"] = Lead.Stage.choices
        ctx["action"] = "create"
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "نام سرنخ را وارد کنید.")
            return redirect("dashboard:crm:lead-create")
        lead = Lead.objects.create(
            store=store,
            name=name,
            phone=request.POST.get("phone", "").strip(),
            email=request.POST.get("email", "").strip(),
            source=request.POST.get("source", "manual").strip(),
            stage=request.POST.get("stage", Lead.Stage.NEW),
            note=request.POST.get("note", "").strip(),
        )
        messages.success(request, f"سرنخ «{lead.name}» ایجاد شد.")
        return redirect("dashboard:crm:lead-detail", pk=lead.pk)


# ─── Lead Detail ─────────────────────────────────────────
class LeadDetailView(StoreAccessMixin, TemplateView):
    template_name = "crm/lead_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lead = get_object_or_404(Lead, pk=self.kwargs["pk"], store=self.request.current_store)
        ctx["lead"] = lead
        ctx["tasks"] = lead.tasks.all()
        ctx["activities"] = lead.activities.all()
        ctx["stage_choices"] = Lead.Stage.choices
        return ctx


# ─── Lead Update Stage ────────────────────────────────────
class LeadUpdateStageView(StoreAccessMixin, View):
    def post(self, request, pk, *args, **kwargs):
        lead = get_object_or_404(Lead, pk=pk, store=request.current_store)
        new_stage = request.POST.get("stage")
        if new_stage in Lead.Stage.values:
            lead.stage = new_stage
            lead.save(update_fields=["stage", "updated_at"])
            # Log activity
            ContactActivity.objects.create(
                store=request.current_store,
                lead=lead,
                activity_type=ContactActivity.ActivityType.NOTE,
                description=f"مرحله تغییر کرد به: {lead.get_stage_display()}",
                actor=request.user,
            )
        return redirect("dashboard:crm:lead-kanban")


# ─── Task List ───────────────────────────────────────────
class TaskListView(StoreAccessMixin, ListView):
    template_name = "crm/task_list.html"
    context_object_name = "tasks"
    paginate_by = 25

    def get_queryset(self):
        store = self.request.current_store
        qs = SaleTask.objects.filter(store=store).select_related("lead", "assigned_to")
        done_filter = self.request.GET.get("done", "")
        if done_filter == "0":
            qs = qs.filter(is_done=False)
        elif done_filter == "1":
            qs = qs.filter(is_done=True)
        return qs.order_by("is_done", "due_date", "-priority")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["done_filter"] = self.request.GET.get("done", "")
        return ctx


# ─── Task Create ─────────────────────────────────────────
class TaskCreateView(StoreAccessMixin, TemplateView):
    template_name = "crm/task_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        store = self.request.current_store
        ctx["leads"] = Lead.objects.filter(store=store)
        lead_pk = self.request.GET.get("lead")
        ctx["selected_lead"] = None
        if lead_pk:
            ctx["selected_lead"] = Lead.objects.filter(pk=lead_pk, store=store).first()
        ctx["priority_choices"] = SaleTask.Priority.choices
        return ctx

    def post(self, request, *args, **kwargs):
        store = request.current_store
        title = request.POST.get("title", "").strip()
        if not title:
            messages.error(request, "عنوان وظیفه را وارد کنید.")
            return redirect("dashboard:crm:task-create")
        lead_pk = request.POST.get("lead")
        lead = None
        if lead_pk:
            lead = Lead.objects.filter(pk=lead_pk, store=store).first()
        due_date = request.POST.get("due_date") or None
        task = SaleTask.objects.create(
            store=store,
            lead=lead,
            title=title,
            due_date=due_date,
            priority=request.POST.get("priority", SaleTask.Priority.MEDIUM),
        )
        messages.success(request, f"وظیفه «{task.title}» ایجاد شد.")
        if lead:
            return redirect("dashboard:crm:lead-detail", pk=lead.pk)
        return redirect("dashboard:crm:task-list")


# ─── Task Toggle Done ────────────────────────────────────
class TaskToggleDoneView(StoreAccessMixin, View):
    def post(self, request, pk, *args, **kwargs):
        task = get_object_or_404(SaleTask, pk=pk, store=request.current_store)
        task.is_done = not task.is_done
        task.save(update_fields=["is_done"])
        next_url = request.POST.get("next", "")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect("dashboard:crm:task-list")


# ─── Contact History ─────────────────────────────────────
class ContactHistoryView(StoreAccessMixin, ListView):
    template_name = "crm/contact_history.html"
    context_object_name = "customers"
    paginate_by = 25

    def get_queryset(self):
        store = self.request.current_store
        return Customer.objects.filter(store=store).annotate(
            activity_count=Count("activities")
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        store = self.request.current_store
        ctx["recent_activities"] = ContactActivity.objects.filter(
            store=store
        ).select_related("customer", "lead", "actor")[:20]
        return ctx
