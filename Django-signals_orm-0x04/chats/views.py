# chats/views.py
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

# Imports for caching
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
# from django.views.decorators.vary import vary_on_cookie # If needed, but cache_page handles Vary: Cookie by default

from .models import Conversation, Message # Ensure your models are correctly imported
from .serializers import ConversationSerializer, MessageSerializer # Ensure serializers are correctly imported
from .permissions import IsParticipantOfConversation # Ensure permissions are correctly imported
from .filters import MessageFilter # Ensure filters are correctly imported

User = get_user_model()

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    # pagination handled by defaults

    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsParticipantOfConversation]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Conversation.objects.filter(participants=user).distinct().order_by('-updated_at')
        return Conversation.objects.none()

    def perform_create(self, serializer):
        request_user = self.request.user
        participants_from_request = serializer.validated_data.get('participants', [])
        participant_pks = [p.pk for p in participants_from_request]
        if request_user.pk not in participant_pks:
            participants_from_request.append(request_user)
        serializer.save(participants=participants_from_request)


# Apply method_decorator to the class if you want to decorate methods like 'list', 'retrieve'
# that are provided by the ModelViewSet.
@method_decorator(cache_page(60), name='list') # Cache the 'list' action for 60 seconds
# @method_decorator(vary_on_cookie, name='list') # cache_page includes Vary: Cookie by default
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = MessageFilter
    # pagination handled by defaults

    def get_permissions(self):
        permission_classes = [IsParticipantOfConversation]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Returns messages for the specific conversation identified by 'conversation_pk'
        from the URL, and ensures the requesting user is a participant of that conversation.
        Filtering via django-filter (MessageFilter) will be applied on top of this.
        """
        user = self.request.user
        # Assuming nested routing: /conversations/<conversation_pk>/messages/
        conversation_pk = self.kwargs.get('conversation_pk')

        if not user.is_authenticated:
            return Message.objects.none()

        if not conversation_pk:
            # If not nested, MessageFilter should handle filtering by 'conversation' query param
            # For this example, let's assume if conversation_pk is not in URL, we rely on filter
            # Or, if this view is *only* for nested, raise an error or return none.
            # For caching to be effective on a "list of messages in a conversation",
            # the conversation context must be clear.
            # If relying solely on query param ?conversation=<id> for non-nested:
            # queryset = Message.objects.filter(conversation__participants=user) # Base for any message list
            # The filterset_class (MessageFilter) would then narrow it down.
            # The cache key includes query params, so it would still cache per conversation.
            # However, the task implies a view specifically for ONE conversation's messages.
            # So, the nested approach with conversation_pk is more direct.
            # For a general /messages/ list that can be filtered, caching is more complex
            # as it depends on all filter permutations.
            # This example focuses on caching the specific view of "messages in *a* conversation".
            return Message.objects.none() # Or raise Http404 if conversation_pk is mandatory for this view logic

        # This queryset is for listing messages *within a specific conversation* from the URL.
        # It's suitable for caching as the conversation_pk in the URL changes the cache key.
        queryset = Message.objects.filter(
            conversation_id=conversation_pk,
            conversation__participants=user
        ).select_related('sender').distinct().order_by('sent_at') # Use your timestamp field, e.g., 'sent_at' or 'timestamp'
        # Added select_related('sender') for optimization, assuming sender details are shown.
        
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        conversation_pk = self.kwargs.get('conversation_pk')
        parent_conversation = get_object_or_404(
            Conversation,
            pk=conversation_pk,
            participants=user
        )
        serializer.save(sender=user, conversation=parent_conversation)

    # If you wanted to cache only an overridden list method:
    # @method_decorator(cache_page(60))
    # def list(self, request, *args, **kwargs):
    #     # Your custom list logic here, or just call super
    #     print(f"DEBUG: MessageViewSet list method called for user {request.user}, conversation_pk {kwargs.get('conversation_pk')}")
    #     response = super().list(request, *args, **kwargs)
    #     # You can inspect response.is_rendered and response.content here
    #     # If you add headers like 'X-Cache-Hit': 'True'/'False', it has to be done
    #     # after super().list() and before returning response, but cache_page handles this.
    #     return response