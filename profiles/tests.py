# AI Citation
# Description: Regression tests for event validation, messaging visibility, roster tracking, CIO calendar, event promotion cap, and reminder notifications
# AI Use: Generated with GitHub Copilot on 2026-04-16.
#   Prompt: "Add regression tests to validate past event creation/RSVP blocking, messaging visibility by shared CIO, CIO users joining other CIOs, centralized CIO calendar access, promoted event feed visibility, promotion cap enforcement (3 per 7 days), and upcoming RSVP reminder creation"
# Notes: 8 test methods covering bugs and new features; all tests passing.

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import CIO, Event, Membership, Notification


class ProfileFlowRegressionTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username="owner", password="pw12345")
		self.owner.profile.role = "cio"
		self.owner.profile.save(update_fields=["role"])

		self.member = User.objects.create_user(username="member", password="pw12345")
		self.other = User.objects.create_user(username="other", password="pw12345")

		self.cio = CIO.objects.create(
			name="Robotics Club",
			description="Builds robots",
			created_by=self.owner,
			status="public",
		)

	def test_create_event_rejects_past_datetime(self):
		self.client.login(username="owner", password="pw12345")
		past_input = (timezone.localtime(timezone.now()) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")

		response = self.client.post(
			reverse("profiles:create_event", args=[self.cio.id]),
			{
				"title": "Past Event",
				"description": "Should fail",
				"date": past_input,
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "must be in the future")
		self.assertFalse(Event.objects.filter(title="Past Event").exists())

	def test_rsvp_rejected_for_past_event(self):
		Membership.objects.create(user=self.member, cio=self.cio, status="approved")
		past_event = Event.objects.create(
			title="Old Meetup",
			description="Already happened",
			date=timezone.now() - timedelta(days=1),
			cio=self.cio,
			host=self.owner,
		)

		self.client.login(username="member", password="pw12345")
		response = self.client.post(reverse("profiles:rsvp_event", args=[self.cio.id, past_event.id]))

		self.assertEqual(response.status_code, 302)
		self.assertIn("rsvp=closed", response.url)
		self.assertFalse(past_event.attendees.filter(id=self.member.id).exists())

	def test_inbox_only_shows_users_from_shared_cio(self):
		Membership.objects.create(user=self.member, cio=self.cio, status="approved")

		isolated_owner = User.objects.create_user(username="isolated_owner", password="pw12345")
		isolated_owner.profile.role = "cio"
		isolated_owner.profile.save(update_fields=["role"])
		isolated_cio = CIO.objects.create(
			name="Isolated CIO",
			description="No overlap",
			created_by=isolated_owner,
			status="public",
		)
		Membership.objects.create(user=self.other, cio=isolated_cio, status="approved")

		self.client.login(username="owner", password="pw12345")
		response = self.client.get(reverse("profiles:inbox"))

		self.assertEqual(response.status_code, 200)
		available_usernames = {
			entry["user"].username for entry in response.context["new_chat_users"]
		}
		self.assertIn("member", available_usernames)
		self.assertNotIn("other", available_usernames)

	def test_cio_user_can_request_to_join_other_cio(self):
		other_owner = User.objects.create_user(username="owner2", password="pw12345")
		other_owner.profile.role = "cio"
		other_owner.profile.save(update_fields=["role"])
		target_cio = CIO.objects.create(
			name="Chess Club",
			description="Board games",
			created_by=other_owner,
			status="public",
		)

		self.client.login(username="owner", password="pw12345")
		response = self.client.post(reverse("profiles:request_join", args=[target_cio.id]))

		self.assertEqual(response.status_code, 302)
		self.assertTrue(
			Membership.objects.filter(user=self.owner, cio=target_cio, status="pending").exists()
		)

	def test_cio_calendar_route_available_for_exec(self):
		self.client.login(username="owner", password="pw12345")

		response = self.client.get(reverse("profiles:cio_calendar"))

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "profiles/cio_calendar.html")

	def test_promoted_event_shows_on_member_dashboard(self):
		Membership.objects.create(user=self.member, cio=self.cio, status="approved")
		promoted_event = Event.objects.create(
			title="Public Open House",
			description="Come visit",
			date=timezone.now() + timedelta(days=2),
			cio=self.cio,
			host=self.owner,
			is_promoted=True,
			promoted_at=timezone.now(),
		)

		self.client.login(username="member", password="pw12345")
		response = self.client.get(reverse("profiles:member"))

		self.assertEqual(response.status_code, 200)
		promoted_ids = [event.id for event in response.context["promoted_events"]]
		self.assertIn(promoted_event.id, promoted_ids)

	def test_promote_event_enforces_weekly_cap(self):
		for idx in range(3):
			Event.objects.create(
				title=f"Promo {idx}",
				description="",
				date=timezone.now() + timedelta(days=idx + 1),
				cio=self.cio,
				host=self.owner,
				is_promoted=True,
				promoted_at=timezone.now() - timedelta(days=1),
			)

		target_event = Event.objects.create(
			title="Cap Test Event",
			description="",
			date=timezone.now() + timedelta(days=10),
			cio=self.cio,
			host=self.owner,
		)

		self.client.login(username="owner", password="pw12345")
		response = self.client.post(reverse("profiles:promote_event", args=[self.cio.id, target_event.id]))

		target_event.refresh_from_db()
		self.assertEqual(response.status_code, 302)
		self.assertIn("promote=limit", response.url)
		self.assertFalse(target_event.is_promoted)

	def test_event_reminder_created_for_upcoming_rsvp(self):
		Membership.objects.create(user=self.member, cio=self.cio, status="approved")
		event = Event.objects.create(
			title="Tomorrow Meeting",
			description="Reminder test",
			date=timezone.now() + timedelta(hours=12),
			cio=self.cio,
			host=self.owner,
		)
		event.attendees.add(self.member)

		self.client.login(username="member", password="pw12345")
		response = self.client.get(reverse("profiles:notifications"))

		self.assertEqual(response.status_code, 200)
		self.assertTrue(
			Notification.objects.filter(
				recipient=self.member,
				event=event,
				notification_type="event_reminder",
			).exists()
		)
