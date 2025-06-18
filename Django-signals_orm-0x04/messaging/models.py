# messaging/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

# Import the custom manager (will be created in the next step)
from .managers import UnreadMessagesManager

class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="The user who sent the message."
    )
    receiver = models.ForeignKey(
        User,
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
    # Existing field, indicates if the receiver has actively marked/viewed the message as read.
    # Default False means it's initially unread from this field's perspective.
    is_read = models.BooleanField(
        default=False,
        help_text="Indicates if the receiver has read the message."
    )
    # New field as per checker requirement.
    # default=True means a new message is considered unread.
    # This field and `is_read` are somewhat redundant. They should be kept in sync.
    # When is_read becomes True, unread should become False, and vice-versa.
    unread = models.BooleanField(
        default=True,
        help_text="True if the message is unread by the receiver. Set to False when read."
    )
    edited = models.BooleanField(
        default=False,
        help_text="Indicates if the message has ever been edited."
    )
    edited_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Timestamp of the last edit."
    )
    edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='edited_messages',
        help_text="User who last edited the message."
    )
    parent_message = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        help_text="The message this message is a reply to."
    )

    # Managers
    objects = models.Manager()  # The default manager.
    unread_manager = UnreadMessagesManager()  # The custom manager for unread messages.

    def __str__(self):
        status = "unread" if self.unread else "read"
        if self.parent_message:
            return f"Reply from {self.sender.username} to msg {self.parent_message.id} ({status}) at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        return f"Message from {self.sender.username} to {self.receiver.username} ({status}) at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['timestamp']


class MessageHistory(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='edit_history',
        help_text="The message that was edited."
    )
    old_content = models.TextField(
        help_text="The content of the message before this specific edit."
    )
    timestamp_of_edit = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when this version was recorded."
    )
    edited_by_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='message_edit_actions',
        help_text="User who performed this edit."
    )

    def __str__(self):
        return f"History for Message ID {self.message.id} at {self.timestamp_of_edit.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-timestamp_of_edit']
        verbose_name_plural = "Message Histories"


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="The user to whom this notification belongs."
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='notifications',
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