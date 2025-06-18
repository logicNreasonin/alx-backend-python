# messaging/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    """
    Simplified User serializer for embedding in other serializers.
    """
    class Meta:
        model = User
        fields = ['id', 'username']


class MessageThreadSerializer(serializers.ModelSerializer):
    """
    Serializer for messages, designed to support threaded replies.
    It recursively serializes replies if they are present in the prefetched data.
    """
    sender = UserSimpleSerializer(read_only=True)
    receiver = UserSimpleSerializer(read_only=True)
    # The 'replies' field uses this same serializer to achieve nesting.
    # This relies on efficient prefetching in the view to avoid N+1 queries.
    replies = serializers.SerializerMethodField()
    parent_message_id = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(), source='parent_message', allow_null=True, required=False, write_only=True
    )

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'receiver', 'content', 'timestamp',
            'edited', 'edited_at', 'parent_message', 'parent_message_id', # parent_message for reading, parent_message_id for writing
            'replies'
        ]
        read_only_fields = ['id', 'sender', 'timestamp', 'edited', 'edited_at', 'replies', 'parent_message']

    def get_replies(self, obj):
        """
        Returns serialized direct replies for a message.
        Relies on 'replies' being prefetched on the queryset passed to the serializer.
        If replies were prefetched with their own replies, this creates a nested structure.
        """
        # Check if replies are already prefetched and available in the object's cache
        if hasattr(obj, '_prefetched_objects_cache') and 'replies' in obj._prefetched_objects_cache:
            # Use the prefetched replies
            # Sort them by timestamp as they might not be ordered in prefetch cache
            prefetched_replies = sorted(obj._prefetched_objects_cache['replies'], key=lambda r: r.timestamp)
            return MessageThreadSerializer(prefetched_replies, many=True, context=self.context).data
        # If not prefetched, or to prevent overly deep automatic recursion in some cases:
        # For this example, we only serialize explicitly prefetched replies.
        # An alternative for controlled depth would be to check context for max_depth.
        return []

    def create(self, validated_data):
        # Set sender from the request context
        validated_data['sender'] = self.context['request'].user
        # parent_message is handled by parent_message_id source
        return super().create(validated_data)