# messaging/managers.py
from django.db import models
from django.db.models import Q

class UnreadMessagesManager(models.Manager):
    def get_unread_for_user(self, user):
        """
        Returns a queryset of all messages that are unread by the specified user,
        where the user is the receiver.
        """
        return self.get_queryset().filter(receiver=user, unread=True).order_by('-timestamp')

    def get_unread_for_user_optimized(self, user):
        """
        Returns a queryset of unread messages for the specified user,
        optimized to fetch only necessary fields for list display using MessageThreadSerializer.
        It assumes replies are not deeply nested in this specific "unread list" view.
        """
        return self.get_queryset().filter(
            receiver=user,
            unread=True
        ).select_related(
            'sender',   # For UserSimpleSerializer nested in MessageThreadSerializer
            'receiver'  # For UserSimpleSerializer nested in MessageThreadSerializer
        ).only(
            # Fields from Message model:
            'id', 'content', 'timestamp', 'edited', 'edited_at', 'unread', 'is_read',
            'parent_message_id', # Foreign key ID for parent_message (resolved as PK by serializer)
            # Fields for sender object (for UserSimpleSerializer):
            'sender_id', 'sender__username', # Must match fields in UserSimpleSerializer
            # Fields for receiver object (for UserSimpleSerializer):
            'receiver_id', 'receiver__username' # Must match fields in UserSimpleSerializer
            # Note: The 'replies' field in MessageThreadSerializer is a SerializerMethodField.
            # It will default to an empty list [] if replies are not prefetched,
            # which is suitable for a simple list of unread messages.
        ).order_by('-timestamp') # Show newest unread messages first