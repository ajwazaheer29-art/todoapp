from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "status", "priority", "due_date", "updated_at")
    list_filter = ("status", "priority", "due_date")
    search_fields = ("title", "description", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at", "completed_at")
    date_hierarchy = "created_at"
