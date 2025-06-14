# Django-Chat/messaging/signals.py
from django.db.models.signals import post_save, pre_save, post_delete # Import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User # Import User model
from django.db.models import Q # For complex lookups

from .models import Message, Notification, MessageHistory

@receiver(post_save, sender=Message)
def create_notification_on_new_message(sender, instance, created, **kwargs):
    if created:
        try:
            Notification.objects.create(
                user=instance.receiver,
                message=instance,
                text=f"You have a new message from {instance.sender.username}."
            )
        except Exception as e:
            print(f"ERROR creating notification: {e}")

@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    if instance.pk is None:
        return
    try:
        original_message = Message.objects.get(pk=instance.pk)
    except Message.DoesNotExist:
        return

    if original_message.content != instance.content:
        MessageHistory.objects.create(
            message=original_message,
            old_content=original_message.content
        )
        instance.edited = True

# New signal handler for User post_delete
@receiver(post_delete, sender=User)
def delete_user_related_data(sender, instance, **kwargs):
    """
    Signal handler to delete data related to a User after the user is deleted.
    - Messages sent or received by the user.
    - Notifications for the user.
    - MessageHistory is handled by CASCADE when Messages are deleted.
    """
    user_pk = instance.pk # The user object 'instance' still has its attributes

    # 1. Delete Messages sent or received by the user.
    #    This will also trigger CASCADE delete for related MessageHistory
    #    and message-specific Notifications.
    messages_to_delete = Message.objects.filter(
        Q(sender_id=user_pk) | Q(receiver_id=user_pk)
    )
    # print(f"DEBUG: Deleting {messages_to_delete.count()} messages for user PK {user_pk}.")
    messages_to_delete.delete()

    # 2. Delete Notifications directly associated with the user.
    #    While notifications linked to messages deleted above would also be gone due to
    #    Message.notifications CASCADE, this ensures any direct notifications
    #    (if such a system were in place) or notifications for messages where the user
    #    was the receiver (and these messages were deleted) are cleaned up if the
    #    Notification.user field was the primary link.
    #    With current models, Notification.user is the message.receiver.
    #    This step acts as a failsafe or for broader notification types.
    notifications_to_delete = Notification.objects.filter(user_id=user_pk)
    # print(f"DEBUG: Deleting {notifications_to_delete.count()} notifications for user PK {user_pk}.")
    notifications_to_delete.delete()

    # MessageHistory entries are deleted via CASCADE when their associated Message is deleted.
    # So, no explicit MessageHistory.objects.filter(message__sender_id=user_pk) etc. is needed here
    # if messages are correctly deleted.

    print(f"INFO: Cleaned up related data for deleted user: {instance.username} (PK: {user_pk})")