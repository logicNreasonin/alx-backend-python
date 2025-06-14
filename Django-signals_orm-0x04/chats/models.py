# Django-Chat/messaging/models.py
from django.db import models
from django.conf import settings # To reference AUTH_USER_MODEL
from django.contrib.auth.models import User # Using built-in User model
from django.db.models import Prefetch # For advanced prefetching

class Conversation(models.Model):
    """
    Represents a distinct conversation thread.
    """
    subject = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional subject for the conversation."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject or f"Conversation ID {self.pk}"

    class Meta:
        ordering = ['-updated_at']

# Custom Manager for Messages
class UnreadMessagesManager(models.Manager):
    """
    Custom manager for the Message model to provide specific queries,
    like fetching unread messages for a user.
    """
    def get_unread_for_user(self, user):
        """
        Returns a queryset of messages that are unread by the specified user,
        where the user is the receiver.
        Optimized with select_related and only to fetch necessary fields.
        """
        return self.get_queryset().filter(
            receiver=user,
            is_read=False
        ).select_related(
            'sender',       # For sender's details
            'conversation'  # For conversation context
        ).only(
            # Fields from Message model itself
            'id',
            'content',
            'timestamp',
            'edited',
            'parent_message_id', # ID of the parent message if it's a reply
            # Fields from related Sender (User model)
            'sender__id',
            'sender__username',
            # Fields from related Conversation model
            'conversation__id',
            'conversation__subject',
            # 'is_read' is implicitly False due to the filter, but could be included
            # if the template logic needs to explicitly check it.
        ).order_by('-timestamp') # Show newest unread messages first


class Message(models.Model):
    """
    Represents a message, which can be a top-level message in a conversation
    or a reply to another message.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="The conversation this message belongs to."
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="The user who sent the message."
    )
    # Added receiver field to clearly define who the message is for,
    # making 'is_read' unambiguous for this task.
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages_in_model', # Using a distinct related_name
        help_text="The primary recipient of the message.",
        null=True, # Allow null if a message is broadcast or to a conversation generally
        blank=True
    )
    content = models.TextField(
        help_text="The text content of the message."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the message was sent."
    )
    # The 'read' boolean field as per instructions (using 'is_read' for clarity)
    is_read = models.BooleanField(
        default=False,
        help_text="Indicates if the receiver has read the message."
    )
    edited = models.BooleanField(
        default=False,
        help_text="Indicates if the message has been edited since its creation."
    )
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        help_text="The message this message is a reply to. Null for top-level messages."
    )

    # Standard manager
    objects = models.Manager()
    # Custom manager for unread messages
    unread_manager = UnreadMessagesManager()

    def __str__(self):
        edited_status = " (edited)" if self.edited else ""
        reply_status = f" (reply to MsgID {self.parent_message.pk})" if self.parent_message else ""
        to_user = f" to {self.receiver.username}" if self.receiver else ""
        return (f"MsgID {self.pk} in Conv {self.conversation.pk} from "
                f"{self.sender.username}{to_user}{reply_status}{edited_status}")

    class Meta:
        ordering = ['timestamp']

    # get_all_replies_as_list and get_conversation_with_threaded_messages
    # from previous task would remain here if they are still needed.
    # For brevity in this specific task's answer, they are omitted but should be kept
    # if task 3 is also part of the final models.py.
    # ... (Keep methods from Task 3 if applicable) ...


# Notification and MessageHistory models (assuming they exist from previous tasks)
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
        related_name='notifications_for_message',
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


class MessageHistory(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='edit_history',
        help_text="The message that was edited."
    )
    old_content = models.TextField(
        help_text="The content of the message before this edit."
    )
    edited_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this version was superseded by an edit."
    )

    def __str__(self):
        return f"Edit history for Message ID {self.message.pk} at {self.edited_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-edited_at']
        verbose_name_plural = "Message Histories"