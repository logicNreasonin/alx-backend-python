# messaging_app/chats/views.py
from rest_framework import viewsets, status, serializers # Ensure serializers is imported
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404 # Useful for fetching objects

from django_filters.rest_framework import DjangoFilterBackend

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation # Ensure this permission can handle nested context
from .filters import MessageFilter

User = get_user_model()

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    # pagination handled by defaults

    def get_permissions(self):
        # For 'list' and 'create', permissions are typically IsAuthenticated (default if specified globally)
        # For instance-specific actions, we check if the user is a participant.
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsParticipantOfConversation]
        else:
            # Assuming IsAuthenticated is handled globally or via default_permission_classes
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # Users can only see conversations they are part of.
            return Conversation.objects.filter(participants=user).distinct().order_by('-updated_at')
        return Conversation.objects.none() # Or raise PermissionDenied

    def perform_create(self, serializer):
        # Ensure the creating user is part of the participants list.
        # The ConversationSerializer's validate method should also ensure at least two participants.
        request_user = self.request.user
        
        # 'participants' comes from 'participant_ids' in the serializer via `source='participants'`
        # This validated_data will already have User instances if participant_ids were provided.
        participants_from_request = serializer.validated_data.get('participants', [])
        
        # Convert QuerySet/list of User instances to a list of their PKs for easier checking
        participant_pks = [p.pk for p in participants_from_request]

        if request_user.pk not in participant_pks:
            # Add the request user if they are not already in the list from the request.
            # This is important if participant_ids was not provided or did not include the creator.
            participants_from_request.append(request_user)
        
        # The serializer.save() will use this updated list.
        serializer.save(participants=participants_from_request)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MessageFilter
    # pagination handled by defaults

    def get_permissions(self):
        # For all actions on messages within a conversation, the user must be a participant.
        # IsParticipantOfConversation should be able to check against the conversation_pk from URL kwargs.
        permission_classes = [IsParticipantOfConversation]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Returns messages for the specific conversation identified by 'conversation_pk'
        from the URL, and ensures the requesting user is a participant of that conversation.
        Filtering via django-filter (MessageFilter) will be applied on top of this.
        """
        user = self.request.user
        conversation_pk = self.kwargs.get('conversation_pk') # Get parent conversation_id from URL

        if not user.is_authenticated:
            return Message.objects.none()

        if not conversation_pk:
            # This case should ideally not be hit if routes are set up correctly for nesting.
            # If it is, it means the viewset is accessed without a conversation_pk,
            # which is not the intended use for nested messages.
            # You could return all messages the user has access to, or none.
            # For strict nesting, returning none or raising an error makes sense.
            # However, MessageFilter might still allow filtering by conversation_id if this is hit.
            # For consistency with nesting, we'll assume conversation_pk is present.
            return Message.objects.none() # Or handle as appropriate

        # Base queryset: messages for the specific conversation, where user is a participant.
        # The IsParticipantOfConversation permission should already guard this,
        # but it's good practice to filter here as well for data integrity.
        queryset = Message.objects.filter(
            conversation_id=conversation_pk,
            conversation__participants=user # Ensure user is part of this specific conversation
        ).distinct().order_by('sent_at') # Ensure 'sent_at' is your timestamp field in Message model

        # The django-filter backend (MessageFilter) will further refine this queryset.
        return queryset

    def perform_create(self, serializer):
        """
        Creates a message within the specific conversation identified by 'conversation_pk'.
        The sender is set to the requesting user.
        The conversation is set based on 'conversation_pk' from the URL.
        """
        user = self.request.user
        conversation_pk = self.kwargs.get('conversation_pk')

        # Ensure the conversation exists and the user is a participant.
        # The IsParticipantOfConversation permission should handle this for the 'create' action.
        # However, an explicit check here before saving is good.
        parent_conversation = get_object_or_404(
            Conversation,
            pk=conversation_pk,
            participants=user # Ensures user is a participant of this specific conversation
        )

        # Set the sender to the current user and the conversation from the URL.
        # The serializer's 'conversation' field might be read-only or not required in input
        # if we are setting it here. Check your MessageSerializer.
        serializer.save(sender=user, conversation=parent_conversation)