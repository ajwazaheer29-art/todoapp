from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Task


class TaskModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alex", password="strong-pass-123")

    def test_completion_timestamp_is_set_and_cleared(self):
        task = Task.objects.create(user=self.user, title="Finish report", status=Task.Status.COMPLETED)
        self.assertIsNotNone(task.completed_at)
        completed_at = task.completed_at
        task.status = Task.Status.IN_PROGRESS
        task.save(update_fields={"status"})
        self.assertIsNone(task.completed_at)
        task.status = Task.Status.COMPLETED
        task.save(update_fields={"status"})
        self.assertGreaterEqual(task.completed_at, completed_at)

    def test_overdue_excludes_completed_tasks(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        pending = Task.objects.create(user=self.user, title="Late", due_date=yesterday)
        done = Task.objects.create(user=self.user, title="Done late", due_date=yesterday, status=Task.Status.COMPLETED)
        self.assertTrue(pending.is_overdue)
        self.assertFalse(done.is_overdue)


class TaskViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="strong-pass-123")
        self.other = User.objects.create_user(username="other", password="strong-pass-123")
        self.task = Task.objects.create(user=self.owner, title="Private task", description="A confidential note")

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("task_list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('task_list')}")

    def test_user_only_sees_their_own_tasks(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("task_list"))
        self.assertNotContains(response, "Private task")

    def test_other_user_cannot_access_task_detail_or_edit_or_delete(self):
        self.client.force_login(self.other)
        for url in (
            reverse("task_detail", args=[self.task.pk]),
            reverse("task_edit", args=[self.task.pk]),
            reverse("task_delete", args=[self.task.pk]),
        ):
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_toggle_requires_post_and_sets_completion_time(self):
        self.client.force_login(self.owner)
        url = reverse("task_toggle", args=[self.task.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)
        self.assertRedirects(response, reverse("task_detail", args=[self.task.pk]))
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.COMPLETED)
        self.assertIsNotNone(self.task.completed_at)

    def test_search_and_combined_filters(self):
        self.client.force_login(self.owner)
        Task.objects.create(user=self.owner, title="Plan", priority=Task.Priority.HIGH)
        response = self.client.get(reverse("task_list"), {"q": "confidential", "priority": "medium"})
        self.assertContains(response, "Private task")
        self.assertNotContains(response, "Plan")

    def test_create_assigns_authenticated_owner(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("task_create"), {"title": "New work", "priority": "urgent", "status": "pending", "description": "", "due_date": ""})
        self.assertEqual(response.status_code, 302)
        created = Task.objects.get(title="New work")
        self.assertEqual(created.user, self.owner)
