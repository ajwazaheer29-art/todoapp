from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Case, Count, IntegerField, Q, When
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import RegistrationForm, TaskForm
from .models import Task


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("task_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("task_list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Welcome to Daymark. Your account is ready.")
        return response


def task_queryset(user):
    return Task.objects.filter(user=user)


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 12

    def get_queryset(self):
        queryset = task_queryset(self.request.user)
        params = self.request.GET
        query = params.get("q", "").strip()[:120]
        status = params.get("status", "")
        priority = params.get("priority", "")
        due = params.get("due", "")

        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
        if status in Task.Status.values:
            queryset = queryset.filter(status=status)
        if priority in Task.Priority.values:
            queryset = queryset.filter(priority=priority)

        today = timezone.localdate()
        if due == "today":
            queryset = queryset.filter(due_date=today)
        elif due == "upcoming":
            queryset = queryset.filter(due_date__gt=today).exclude(status=Task.Status.COMPLETED)
        elif due == "overdue":
            queryset = queryset.filter(due_date__lt=today).exclude(status=Task.Status.COMPLETED)

        sort = params.get("sort", "newest")
        if sort == "oldest":
            queryset = queryset.order_by("created_at", "pk")
        elif sort == "due_date":
            queryset = queryset.order_by("due_date", "-created_at", "pk")
        elif sort == "priority":
            rank = Case(
                When(priority=Task.Priority.URGENT, then=0),
                When(priority=Task.Priority.HIGH, then=1),
                When(priority=Task.Priority.MEDIUM, then=2),
                default=3,
                output_field=IntegerField(),
            )
            queryset = queryset.annotate(priority_rank=rank).order_by("priority_rank", "due_date", "-created_at")
        elif sort == "title":
            queryset = queryset.order_by("title", "pk")
        elif sort == "updated":
            queryset = queryset.order_by("-updated_at", "pk")
        else:
            sort = "newest"
            queryset = queryset.order_by("-created_at", "-pk")
        self.selected_sort = sort
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_tasks = task_queryset(self.request.user)
        today = timezone.localdate()
        stats = user_tasks.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status=Task.Status.PENDING)),
            in_progress=Count("id", filter=Q(status=Task.Status.IN_PROGRESS)),
            completed=Count("id", filter=Q(status=Task.Status.COMPLETED)),
            overdue=Count("id", filter=Q(due_date__lt=today) & ~Q(status=Task.Status.COMPLETED)),
        )
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context.update(
            stats=stats,
            query=self.request.GET.get("q", "").strip()[:120],
            selected_status=self.request.GET.get("status", ""),
            selected_priority=self.request.GET.get("priority", ""),
            selected_due=self.request.GET.get("due", ""),
            selected_sort=getattr(self, "selected_sort", self.request.GET.get("sort", "newest")),
            today=today,
            filter_query=query_params.urlencode(),
        )
        return context


class TaskOwnerMixin(LoginRequiredMixin):
    def get_queryset(self):
        return task_queryset(self.request.user)


class TaskDetailView(TaskOwnerMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, "Task created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("task_detail", kwargs={"pk": self.object.pk})


class TaskUpdateView(TaskOwnerMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Your changes have been saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("task_detail", kwargs={"pk": self.object.pk})


class TaskDeleteView(TaskOwnerMixin, DeleteView):
    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("task_list")

    def form_valid(self, form):
        messages.success(self.request, "Task deleted.")
        return super().form_valid(form)


class TaskToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(task_queryset(request.user), pk=pk)
        if task.status == Task.Status.COMPLETED:
            task.status = Task.Status.PENDING
            message = "Task reopened and moved to pending."
        else:
            task.status = Task.Status.COMPLETED
            message = "Task marked as complete. Nice work!"
        task.save()
        messages.success(request, message)
        next_url = request.POST.get("next", "")
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("task_detail", pk=task.pk)
