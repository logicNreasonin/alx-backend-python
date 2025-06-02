# messaging_app/chats/views.py
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
# IsAuthenticated and PageNumberPagination are applied by default from settings.py
from django.contrib.auth import get_user_model
from django.db.models import Q

from django_filters.rest_framework import DjangoFilterBackend # Import DjangoFilterBackend

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation
from .filters import MessageFilter # Import your MessageFilter

User = get_user_model()

class ConversationViewSet(viewsets.ModelViewSet):
    # ... (ConversationViewSet code remains the same, pagination will apply if listing many) ...
    # For brevity, I'm omitting the full ConversationViewSet code here, assuming no changes other than
    # pagination automatically applying if it ever lists enough items.
    serializer_class = ConversationSerializer

    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsParticipantOfConversation]
        else:
            permission_classes = [] 
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(participants=user).distinct().order_by('-updated_at')

    def perform_create(self, serializer):
        initial_participants_qs = serializer.validated_data.get('participants', User.objects.none())
        participant_list = list(initial_participants_qs)
        request_user = self.request.user
        if request_user not in participant_list:
            participant_list.append(request_user)
        serializer.save(participants=participant_list)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    # Pagination is handled by DEFAULT_PAGINATION_CLASS in settings.py
    
    # Add filter backends and specify the filterset class
    filter_backends = [DjangoFilterBackend] # Add other backends if needed (e.g., SearchFilter, OrderingFilter)
    filterset_class = MessageFilter

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsParticipantOfConversation]
        elif self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsParticipantOfConversation]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Base queryset: Only messages from conversations the user is a participant in.
        Filtering via django-filter will be applied on top of this.
        The specific 'conversation_id' query param handling can be removed if
        the filterset's 'conversation' filter is preferred and sufficient.
        However, keeping it can be useful for a direct, common filter.
        For this exercise, we'll rely on django-filter for conversation filtering.
        """
        user = self.request.user
        # Base queryset: all messages from conversations the user is part of.
        queryset = Message.objects.filter(conversation__participants=user).distinct().order_by('timestamp')
        
        # The django-filter backend will further refine this queryset based on query parameters
        # defined in MessageFilter (e.g., ?conversation=<id>, ?sender=<id>, ?timestamp_after=...)
        return queryset

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)