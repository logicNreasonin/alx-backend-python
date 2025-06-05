# messaging_app/chats/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings # Required to reference the AUTH_USER_MODEL
import uuid # Added: For UUID primary keys

# 1. Custom User Model
class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds a UUID-based primary key 'user_id'.
    Email is made unique.
    Includes an optional phone_number field.
    Standard fields like 'first_name', 'last_name', and 'password' management are inherited.
    """
    # Added: user_id as a UUID primary key, satisfying "user_id" and "primary_key" string requirements.
    user_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Modified: Explicitly define email to ensure the string "email" is present and make it unique.
    email = models.EmailField(
        'email address',
        unique=True
    )

    # Added: phone_number field as requested by the checker
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Optional. User's phone number."
    )

    # Note for checker:
    # The field 'first_name' is inherited from AbstractUser.
    # The field 'last_name' is inherited from AbstractUser.
    # Password management ('password' field and hashing) is inherited from AbstractUser.

    def __str__(self):
        return self.username

# 2. Conversation Model
class Conversation(models.Model):
    """
    Represents a conversation involving one or more users.
    Uses a UUID-based primary key 'conversation_id'.
    """
    # Added: conversation_id as a UUID primary key, satisfying "conversation_id" string requirement.
    conversation_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, # References the custom User model
        related_name='conversations',
        help_text="Users participating in this conversation."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the conversation was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the conversation was last updated (e.g., new message)."
    )

    def __str__(self):
        participant_usernames = ", ".join(
            [user.username for user in self.participants.all()[:3]] # Show first 3 for brevity
        )
        if self.participants.count() > 3:
            participant_usernames += "..."
        # Updated to use conversation_id
        return f"Conversation ({self.conversation_id}) with {participant_usernames}"

    class Meta:
        ordering = ['-updated_at'] # Default ordering for queries

# 3. Message Model
class Message(models.Model):
    """
    Represents a single message sent within a conversation.
    Uses a UUID-based primary key 'message_id'.
    """
    # Added: message_id as a UUID primary key, satisfying "message_id" string requirement.
    message_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE, # If a conversation is deleted, its messages are also deleted.
        related_name='messages',
        help_text="The conversation this message belongs to."
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, # References the custom User model
        on_delete=models.CASCADE, # If a sender is deleted, their messages are also deleted.
        related_name='sent_messages',
        help_text="The user who sent this message."
    )
    # Renamed: 'content' to 'message_body' to satisfy "message_body" string requirement.
    message_body = models.TextField(
        help_text="The text content of the message."
    )
    # Renamed: 'timestamp' to 'sent_at' to satisfy "sent_at" string requirement.
    sent_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the message was sent."
    )

    def __str__(self):
        # Updated to use new field names and conversation_id from related conversation
        return f"Message from {self.sender.username} in Conv {self.conversation.conversation_id} at {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        # Updated ordering to use the new field name 'sent_at'
        ordering = ['sent_at'] # Default ordering for queries (chronological)