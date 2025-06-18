# messaging/views.py
from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

# Imports for caching
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
# from django.views.decorators.vary import vary_on_cookie # cache_page includes Vary: Cookie by default

from .models import Message
# Assuming MessageThreadSerializer is in messaging.serializers
# If not, create it or adjust import. For this example, let's assume it exists.
from .serializers import MessageThreadSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class DeleteUserView(viewsets.ViewSet): # Adapted to ViewSet for potential router usage
    permission_classes = [IsAuthenticated]
    @action(detail=False, methods=['delete'], url_path='delete-account', url_name='delete-account')
    def delete_account(self, request, *args, **kwargs):
        user = request.user
        try:
            user_id_for_log = user.id
            username_for_log = user.username
            user.delete() # Triggers post_delete signal
            logger.info(f"User account for {username_for_log} (ID: {user_id_for_log}) deleted successfully.")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting user account for {getattr(user, 'username', 'N/A')}: {e}", exc_info=True)
            return Response({"error": "An error occurred while deleting the account."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageViewSet(viewsets.ModelViewSet):
    """
    General API endpoint for messages (creating, retrieving single threads, unread inbox).
    """
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Base queryset - further filtered by actions.
        return Message.objects.filter(Q(sender=user) | Q(receiver=user) | Q(replies__sender=user) | Q(replies__receiver=user)).distinct()

    def _get_optimized_replies_queryset(self, depth=2):
        queryset = Message.objects.select_related('sender', 'receiver').order_by('timestamp')
        if depth <= 0:
            return queryset
        current_prefetch = None
        for _ in range(depth):
            if current_prefetch is None:
                current_prefetch = Prefetch('replies', queryset=queryset)
            else:
                current_prefetch = Prefetch('replies', queryset=queryset.prefetch_related(current_prefetch))
        return current_prefetch

    def list(self, request, *args, **kwargs):
        """
        List top-level messages (not replies) for the authenticated user across all their conversations.
        """
        user = request.user
        queryset = Message.objects.filter(
            Q(parent_message__isnull=True) & (Q(sender=user) | Q(receiver=user))
        ).select_related(
            'sender', 'receiver'
        ).prefetch_related(
            Prefetch('replies', queryset=Message.objects.select_related('sender', 'receiver').order_by('timestamp'))
        ).order_by('-timestamp')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        Retrieve a specific message, including its threaded replies.
        Marks the message as read if the current user is the receiver.
        """
        user = request.user
        prefetch_depth = 2
        base_message_qs = Message.objects.select_related(
            'sender', 'receiver', 'parent_message', 'parent_message__sender', 'parent_message__receiver'
        )
        replies_prefetch_obj = self._get_optimized_replies_queryset(depth=prefetch_depth)
        
        if replies_prefetch_obj:
            queryset = base_message_qs.prefetch_related(replies_prefetch_obj)
        else:
            queryset = base_message_qs
        
        instance = get_object_or_404(queryset, Q(pk=pk) & (Q(sender=user) | Q(receiver=user) | Q(replies__sender=user) | Q(replies__receiver=user))).distinct()

        if instance.receiver == user and instance.unread:
            instance.unread = False
            instance.is_read = True
            instance.save(update_fields=['unread', 'is_read'])
            logger.info(f"Message {instance.id} marked as read for user {user.username}")

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='unread-inbox', permission_classes=[IsAuthenticated])
    def unread_inbox(self, request):
        user = request.user
        unread_messages_qs = Message.unread_manager.get_unread_for_user_optimized(user)
        page = self.paginate_queryset(unread_messages_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(unread_messages_qs, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        if 'receiver' not in serializer.validated_data and not serializer.validated_data.get('parent_message'):
            raise serializers.ValidationError("Either 'receiver' or 'parent_message' must be provided.")
        parent_msg_obj = serializer.validated_data.get('parent_message')
        current_user = self.request.user
        receiver = serializer.validated_data.get('receiver')
        if not receiver and parent_msg_obj:
            if parent_msg_obj.sender == current_user:
                receiver = parent_msg_obj.receiver
            else:
                receiver = parent_msg_obj.sender
        if not receiver:
             raise serializers.ValidationError("Could not determine receiver for the message.")
        serializer.save(sender=current_user, receiver=receiver)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# New ViewSet specifically for listing messages in a conversation with another user
# This ViewSet's 'list' action will be cached.
@method_decorator(cache_page(60), name='list')
class UserConversationHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for displaying messages in a conversation between the authenticated user
    and another specified user. The list view is cached for 60 seconds.
    The 'other_user_pk' is expected to be part of the URL.
    """
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated]

    # Helper method (can be utility or part of a base class if used elsewhere)
    def _get_optimized_replies_queryset_for_conversation(self, depth=1):
        # Optimized for conversation listing; sender/receiver are specific to the reply
        queryset = Message.objects.select_related('sender', 'receiver').order_by('timestamp')
        if depth <= 0:
            return queryset
        current_prefetch = None
        for _ in range(depth):
            if current_prefetch is None:
                current_prefetch = Prefetch('replies', queryset=queryset)
            else:
                current_prefetch = Prefetch('replies', queryset=queryset.prefetch_related(current_prefetch))
        return current_prefetch

    def get_queryset(self):
        """
        Returns a queryset of top-level messages exchanged between the authenticated user
        and the user specified by 'other_user_pk' in the URL kwargs.
        Replies are prefetched.
        """
        request_user = self.request.user
        other_user_pk = self.kwargs.get('other_user_pk')

        if not other_user_pk:
            logger.warning("UserConversationHistoryViewSet: other_user_pk not provided in URL.")
            return Message.objects.none()

        try:
            # Ensure other_user_pk is an integer if your PKs are integers
            other_user_pk = int(other_user_pk)
            other_user = User.objects.get(pk=other_user_pk)
        except (ValueError, User.DoesNotExist):
            logger.warning(f"UserConversationHistoryViewSet: User with pk {other_user_pk} not found or invalid PK.")
            return Message.objects.none() # Or raise Http404

        if request_user == other_user:
            logger.info(f"UserConversationHistoryViewSet: User {request_user.username} attempting to view conversation with self.")
            # Depending on requirements, could return empty or allow viewing self-messages if they exist.
            # For a typical "conversation with other", this is usually empty or an error.
            return Message.objects.none()

        # Query for top-level messages in this specific conversation
        queryset = Message.objects.filter(
            Q(parent_message__isnull=True) &
            (
                (Q(sender=request_user) & Q(receiver=other_user)) |
                (Q(sender=other_user) & Q(receiver=request_user))
            )
        ).select_related(
            'sender', 'receiver'  # For the top-level message itself
        ).order_by('timestamp')   # Chronological order for conversation display

        # Prefetch replies for these top-level messages
        prefetch_depth = 1 # Adjust as needed for performance vs. detail
        replies_prefetch_obj = self._get_optimized_replies_queryset_for_conversation(depth=prefetch_depth)
        if replies_prefetch_obj:
            queryset = queryset.prefetch_related(replies_prefetch_obj)
        
        logger.debug(f"UserConversationHistoryViewSet: Querying messages between {request_user.username} and {other_user.username}")
        return queryset

    # The 'list' method is provided by ReadOnlyModelViewSet and will use the get_queryset above.
    # The @method_decorator(cache_page(60), name='list') applies to this inherited 'list' method.