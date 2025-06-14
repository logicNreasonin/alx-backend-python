# messaging/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings # If using custom user
# from django.contrib.auth import get_user_model # If using custom user

from .models import Message, Notification

# User = get_user_model() # If using custom user

@receiver(post_save, sender=Message)
def create_notification_on_new_message(sender, instance, created, **kwargs):
    """
    Signal handler to create a Notification when a new Message is saved.
    """
    if created:  # Only run if a new Message instance was created
        try:
            Notification.objects.create(
                user=instance.receiver,  # The user who received the message
                message=instance,        # Link the notification to the message
                text=f"You have a new message from {instance.sender.username}."
            )
            print(f"DEBUG: Notification created for {instance.receiver.username} regarding message ID {instance.id}") # For console debugging
        except Exception as e:
            # It's good practice to log errors in signal handlers
            # to avoid silent failures.
            print(f"ERROR creating notification: {e}")