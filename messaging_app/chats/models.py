# messaging_app/chats/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings # Required to reference the AUTH_USER_MODEL

# 1. Custom User Model
class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    This allows you to add custom fields to the user profile in the future
    if needed (e.g., profile_picture, phone_number, bio).
    For now, it serves as the designated user model for the project.
    """
    # Add any additional user fields here if required by your specific schema.
    # For example:
    # bio = models.TextField(blank=True, null=True)
    # profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.username

# 2. Conversation Model
class Conversation(models.Model):
    """
    Represents a conversation involving one or more users.
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
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
        # Provides a more readable representation in Django admin or shell
        participant_usernames = ", ".join(
            [user.username for user in self.participants.all()[:3]] # Show first 3 for brevity
        )
        if self.participants.count() > 3:
            participant_usernames += "..."
        return f"Conversation ({self.pk}) with {participant_usernames}"

    class Meta:
        ordering = ['-updated_at'] # Default ordering for queries

# 3. Message Model
class Message(models.Model):
    """
    Represents a single message sent within a conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE, # If a conversation is deleted, its messages are also deleted.
        related_name='messages',
        help_text="The conversation this message belongs to."
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # If a sender is deleted, their messages are also deleted.
                                  # Consider models.SET_NULL if you want to keep messages but mark sender as null.
        related_name='sent_messages',
        help_text="The user who sent this message."
    )
    content = models.TextField(
        help_text="The text content of the message."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the message was sent."
    )
    # Optional: you can add a field to track if a message has been read
    # is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} in Conv {self.conversation.pk} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['timestamp'] # Default ordering for queries (chronological)