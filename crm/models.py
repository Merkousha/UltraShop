from django.db import models


class Lead(models.Model):
    class Stage(models.TextChoices):
        NEW = "new", "سرنخ جدید"
        CONTACTED = "contacted", "تماس گرفته شد"
        NEGOTIATION = "negotiation", "در حال مذاکره"
        WON = "won", "موفق"
        LOST = "lost", "ناموفق"

    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="leads")
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    source = models.CharField(
        max_length=50, blank=True, default="",
        help_text="contact_form, chat, manual"
    )
    stage = models.CharField(max_length=15, choices=Stage.choices, default=Stage.NEW)
    note = models.TextField(blank=True, default="")
    assigned_to = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_leads"
    )
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leads"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crm_leads"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.get_stage_display()}"


class SaleTask(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "کم"
        MEDIUM = "medium", "متوسط"
        HIGH = "high", "زیاد"

    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="sale_tasks")
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, null=True, blank=True, related_name="tasks"
    )
    title = models.CharField(max_length=300)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    is_done = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sale_tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "crm_sale_tasks"
        ordering = ["due_date", "-priority"]

    def __str__(self):
        return self.title


class ChatSession(models.Model):
    """Browser chat session with AI assistant on the storefront."""
    store = models.ForeignKey("core.Store", on_delete=models.CASCADE, related_name="chat_sessions")
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="chat_sessions"
    )
    session_key = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_sessions"
        unique_together = [("store", "session_key")]

    def __str__(self):
        return f"ChatSession {self.session_key[:12]}… @ {self.store.name}"


class ChatMessage(models.Model):
    """A single message in a storefront chat session."""

    class Role(models.TextChoices):
        USER = "user", "کاربر"
        ASSISTANT = "assistant", "دستیار"

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class ContactActivity(models.Model):
    class ActivityType(models.TextChoices):
        ORDER = "order", "سفارش"
        NOTE = "note", "یادداشت"
        CALL = "call", "تماس"
        EMAIL = "email", "ایمیل"
        CHAT = "chat", "چت"

    store = models.ForeignKey(
        "core.Store", on_delete=models.CASCADE, related_name="contact_activities"
    )
    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="activities"
    )
    lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="activities"
    )
    activity_type = models.CharField(max_length=10, choices=ActivityType.choices)
    description = models.TextField(blank=True, default="")
    reference_id = models.CharField(
        max_length=100, blank=True, default="",
        help_text="e.g. order pk"
    )
    actor = models.ForeignKey(
        "core.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "crm_contact_activities"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.activity_type} — {self.created_at:%Y-%m-%d}"
