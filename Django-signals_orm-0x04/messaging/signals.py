from django.db.models.signals import post_save, pre_save, post_delete # Added post_delete
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model # For User model in post_delete signal
from django.db.models import Q # For OR queries in filters

from .models import Message, Notification, MessageHistory

User = get_user_model() # Get the currently active User model

@receiver(pre_save, sender=Message)
def log_message_edit_history(sender, instance, **kwargs):
    """
    Signal handler to log the old content of a message into MessageHistory
    before it's updated if the content has changed.
    It also updates the 'edited', 'edited_at', and potentially 'edited_by'
    fields on the Message instance itself.
    """
    if instance.pk:  # Check if this is an update (instance already has a primary key)
        try:
            original_message = Message.objects.get(pk=instance.pk)
            # Check if content has actually changed to avoid creating history for non-content updates
            if original_message.content != instance.content:
                # Create a history entry with the *old* content
                MessageHistory.objects.create(
                    message=original_message,  # Link to the message being edited
                    old_content=original_message.content,  # Store the content *before* this save
                    # timestamp_of_edit is set by default=timezone.now in MessageHistory model
                    # If instance.edited_by is set by the view before save(), it will be recorded.
                    edited_by_user=getattr(instance, 'edited_by', None) # Safely access edited_by
                )
                # Mark the message instance (which is about to be saved) as edited
                instance.edited = True
                instance.edited_at = timezone.now()
                # Note: instance.edited_by should ideally be set in the view
                # handling the update, e.g., message.edited_by = request.user.
                # The signal then uses this value if available.
        except Message.DoesNotExist:
            # This case should ideally not be reached if instance.pk is not None.
            # Handle defensively or log if necessary.
            pass
        except Exception as e:
            # It's good practice to log errors in signal handlers.
            # For now, printing to console. For production, use logging.
            print(f"ERROR in log_message_edit_history signal: {e}")


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
        except Exception as e:
            # It's good practice to log errors in signal handlers
            # to avoid silent failures.
            print(f"ERROR creating notification: {e}")


@receiver(post_delete, sender=User)
def delete_user_related_data(sender, instance, **kwargs):
    """
    Signal handler to delete all messages, notifications, and message histories
    associated with a user when their account is deleted.
    'instance' is the User object that was deleted.
    """
    user_being_deleted = instance

    # 1. Delete Messages sent or received by the user.
    # Note: If MessageHistory.message has on_delete=models.CASCADE (which it should),
    # deleting these messages will automatically delete their associated histories.
    messages_qs = Message.objects.filter(Q(sender=user_being_deleted) | Q(receiver=user_being_deleted))
    deleted_message_count, _ = messages_qs.delete()
    print(f"DEBUG: Deleted {deleted_message_count} messages for user {user_being_deleted.username}")

    # 2. Delete Notifications for the user.
    notifications_qs = Notification.objects.filter(user=user_being_deleted)
    deleted_notification_count, _ = notifications_qs.delete()
    print(f"DEBUG: Deleted {deleted_notification_count} notifications for user {user_being_deleted.username}")

    # 3. Delete MessageHistory entries where this user was the editor ('edited_by_user').
    # This cleans up history entries for messages that might not have been deleted
    # in step 1 (e.g., if the user edited a message but wasn't sender/receiver).
    # This also handles cases where MessageHistory.edited_by_user was SET_NULL
    # but we want to remove the history entry entirely if the editor is deleted.
    history_qs = MessageHistory.objects.filter(edited_by_user=user_being_deleted)
    deleted_history_count, _ = history_qs.delete()
    print(f"DEBUG: Deleted {deleted_history_count} message edit histories made by user {user_being_deleted.username}")