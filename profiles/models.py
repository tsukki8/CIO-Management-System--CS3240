# AI Citation
# Description: Profile model
# AI Use: Generated with ChatGPT.
#   Prompt: "How to build a Django profile model that contains different user types?"
# Notes: Used to help write code for the initial Profile class, part of it was modified during development process.

# AI Citation
# Description: CIO, Membership, and Event models
# AI Use: Generated with GitHub Copilot on 2026-03-29.
#   Prompt: "Build CIO model with public/hidden status, image field, plus Membership and Event models"
# Notes: Status choices, image_url fields for future S3 integration

# AI Citation
# Description: Direct messaging feature
# AI Use: Assisted with ChatGPT on 2026-04-13 - modified with GitHub Copilot.
#   Prompt: "Help provide a starting point to implement a basic messaging system in Django."
# Notes: Created DM(Chat) featuer allowing messaging between users to happen.

# AI Citation
# Description: Event promotion fields and event reminder notification support
# AI Use: Generated with GitHub Copilot on 2026-04-16.
#   Prompt: "Add is_promoted and promoted_at fields to Event model, extend Notification model to support event reminders with event ForeignKey"
# Notes: Enables event promotion tracking, rolling 7-day promotion cap enforcement, and in-app event reminder notifications for RSVPs.

# AI Citation
# Description: Unread notification feature
# AI Use: Assisted with ChatGPT on 2026-04-28 - modified with GitHub Copilot..
#   Prompt: "Help provide a starting point to add basic unread in-app notifications for new messages in Django."
# Notes: Added notifications for unread messages

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

# Create your models here.
class Profile(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),   # normal users
        ('cio', 'CIO'),     # cio
        ('admin', 'User Administrator'),    #admin
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='member',
        blank=True,
        null = True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True )

    # To-string method for class Profile
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
class CIO(models.Model):
    STATUS_CHOICES=[
        ('public', 'Public'),
        ('hidden', 'Hidden'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='hidden')
    profile_picture = models.ImageField(upload_to='cio_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cios')

    # to string
    def __str__(self):
        return self.name
    
class Membership(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cio = models.ForeignKey(CIO, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.user.username} -> {self.cio.name} ({self.status})"


class CIORequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cio_requests')
    application_text = models.TextField(blank=True, default="")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} -> CIO ({self.status})"
    

class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date = models.DateTimeField()

    cio = models.ForeignKey(CIO, on_delete=models.CASCADE, related_name='events')

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hosted_events"
    )

    attendees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="events_attending"
    )

    is_promoted = models.BooleanField(default=False)
    promoted_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Conversation(models.Model):
    users = models.ManyToManyField(User, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        usernames = ", ".join(user.username for user in self.users.all())
        return f"Conversation {self.id}: {usernames}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("message", "Message"),
        ("event_reminder", "Event Reminder"),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_notifications"
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default="message"
    )
    text = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.username} - {self.text}"
    
# Automatically create a profile when a user is created
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, role='member')
