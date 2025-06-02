# messaging_app/chats/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()  # Fetches the custom User model ('chats.User')

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    """
    class Meta:
        model = User
        # Define fields to be included in the serialized representation
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        # You might want to make some fields read-only if users are created via a separate mechanism
        # or if you have a specific registration endpoint.
        # Example: read_only_fields = ['id']


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Message model.
    """
    # Display sender's username for readability instead of just the ID.
    # This field will be read-only; the sender is typically set by the view based on request.user.
    sender = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'timestamp']
        # 'sender' is read-only as it's set by the view logic (e.g., request.user).
        # 'timestamp' is auto-generated.
        read_only_fields = ['id', 'sender', 'timestamp']
        # 'conversation' (ForeignKey) will default to PrimaryKeyRelatedField,
        # allowing you to pass a conversation ID when creating a message.
        # 'content' is writable.

    def create(self, validated_data):
        # If the sender is not automatically set by the view context,
        # you would set it here, e.g., if it's passed in validated_data
        # or from self.context['request'].user.
        # For now, assuming the view will handle setting the sender.
        return super().create(validated_data)


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Conversation model.
    Handles nested serialization of participants and messages.
    """
    # For displaying participants with their full details (read-only).
    # Uses UserSerializer for each participant.
    participants = UserSerializer(many=True, read_only=True)

    # For accepting a list of user IDs when creating/updating a conversation's participants.
    # This field is write-only and maps to the 'participants' model field.
    participant_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True,
        source='participants',  # Links this input to the 'participants' M2M field on the model
        help_text="List of user IDs to include in the conversation."
    )

    # For displaying messages within a conversation (read-only).
    # Uses MessageSerializer for each message.
    # The 'messages' field on the serializer maps to the related_name 'messages'
    # from Message.conversation ForeignKey.
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id',
            'participants',      # For reading participant details
            'participant_ids',   # For writing participant IDs
            'messages',          # For reading messages in the conversation
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    # DRF's ModelSerializer handles M2M relationships well.
    # When creating or updating a Conversation instance, if 'participant_ids'
    # is provided in the input data, the `source='participants'` setting ensures
    # that the 'participants' M2M field on the Conversation model is correctly
    # populated or updated. No custom .create() or .update() is needed for this
    # specific M2M handling if using 'source'.