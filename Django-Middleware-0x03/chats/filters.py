# messaging_app/chats/filters.py
import django_filters
from .models import Message, Conversation

class MessageFilter(django_filters.FilterSet):
    """
    FilterSet for the Message model.
    """
    # Filter messages sent after a specific timestamp
    timestamp_after = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr='gte')
    
    # Filter messages sent before a specific timestamp
    timestamp_before = django_filters.DateTimeFilter(field_name="timestamp", lookup_expr='lte')
    
    # Filter messages by sender's username (case-insensitive)
    # This is more user-friendly than sender ID for query params.
    sender_username = django_filters.CharFilter(field_name='sender__username', lookup_expr='iexact')

    # Filter messages by conversation ID
    # conversation_id = django_filters.NumberFilter(field_name='conversation__id') # Alternative to query_params

    class Meta:
        model = Message
        fields = {
            'conversation': ['exact'], # Allows filtering by ?conversation=<id>
            'sender': ['exact'],       # Allows filtering by ?sender=<id> (user ID)
            # 'content': ['icontains'],  # Optional: if you want to filter by message content
        }
        # The fields dictionary is a shorthand. For more complex lookups (like date ranges
        # or related field lookups like sender_username), define them explicitly as above.