# messaging/models.py
from django.db import models
from django.conf import settings # To reference AUTH_USER_MODEL
from django.contrib.auth.models import User # Using built-in User model for simplicity

# If you were using a custom user model, you would import it like:
# from django.contrib.auth import get_user_model
# User = get_user_model()

class Message(models.Model):
    """
    Represents a message sent from one user to another.
    """
    sender = models.ForeignKey(
        User, # Or settings.AUTH_USER_MODEL if using custom user
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="The user who sent the message."
    )
    receiver = models.ForeignKey(
        User, # Or settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='received_messages',
        help_text="The user who will receive the message."
    )
    content = models.TextField(
        help_text="The text content of the message."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the message was sent."
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Indicates if the receiver has read the message."
    )

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-timestamp']


class Notification(models.Model):
    """
    Represents a notification for a user, typically about a new message.
    """
    user = models.ForeignKey(
        User, # Or settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="The user to whom this notification belongs."
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='notifications', # Allows Message.notifications.all()
        help_text="The message that triggered this notification."
    )
    text = models.CharField(
        max_length=255,
        help_text="The content of the notification."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the notification was created."
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Indicates if the user has read the notification."
    )

    def __str__(self):
        return f"Notification for {self.user.username}: '{self.text[:50]}...'"

    class Meta:
        ordering = ['-created_at']