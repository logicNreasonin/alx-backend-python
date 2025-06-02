# messaging_app/chats/views.py
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

User = get_user_model()

class ConversationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows conversations to be viewed or created.
    - Lists conversations for the authenticated user.
    - Creates new conversations, automatically adding the authenticated user
      as a participant.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view returns a list of all conversations
        for the currently authenticated user.
        """
        user = self.request.user
        # Users can only see conversations they are participants in.
        return Conversation.objects.filter(participants=user).distinct().order_by('-updated_at')

    def perform_create(self, serializer):
        """
        Custom logic for creating a conversation.
        The authenticated user (request.user) is automatically added as a participant.
        The `participant_ids` field in the serializer (source='participants') provides
        the initial list of participants.
        """
        # `serializer.validated_data['participants']` exists because `participant_ids`
        # in the serializer has `source='participants'`. It's a QuerySet of User objects.
        initial_participants_qs = serializer.validated_data.get('participants', User.objects.none())
        participant_list = list(initial_participants_qs)

        request_user = self.request.user
        if request_user not in participant_list:
            participant_list.append(request_user)

        # The serializer's save method will handle setting the M2M relationship
        # when 'participants' (the model field name) is passed as a kwarg.
        serializer.save(participants=participant_list)

class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows messages to be viewed or created.
    - Lists messages, filterable by `conversation_id`. Users can only see
      messages in conversations they are part of.
    - Creates new messages, setting the sender to the authenticated user.
      The user must be a participant in the conversation.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view returns messages based on user participation and
        optional `conversation_id` query parameter.
        """
        user = self.request.user
        conversation_id = self.request.query_params.get('conversation_id')

        if conversation_id:
            try:
                # Ensure the user is part of the requested conversation
                conversation = Conversation.objects.get(pk=conversation_id)
                if user not in conversation.participants.all():
                    # User is not part of this conversation, return no messages
                    return Message.objects.none()
                # Return messages for that specific conversation
                return Message.objects.filter(conversation__id=conversation_id).order_by('timestamp')
            except Conversation.DoesNotExist:
                return Message.objects.none() # Conversation not found
        else:
            # If no conversation_id is specified, list all messages from all
            # conversations the user is a participant in.
            # This could be a large list; consider if pagination is sufficient
            # or if conversation_id should be mandatory for production.
            return Message.objects.filter(conversation__participants=user).distinct().order_by('timestamp')


    def perform_create(self, serializer):
        """
        Custom logic for creating a message.
        The sender is automatically set to the authenticated user.
        The user must be a participant of the conversation.
        """
        conversation = serializer.validated_data['conversation'] # This is a Conversation instance
        user = self.request.user

        # Check if the user is a participant of the target conversation
        if user not in conversation.participants.all():
            # Using serializers.ValidationError will result in a 400 Bad Request
            raise serializers.ValidationError(
                {"error": "You are not a participant in this conversation and cannot send messages."}
            )

        # Set the sender to the authenticated user and save the message
        serializer.save(sender=user)