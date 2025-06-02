# messaging_app/chats/permissions.py

from rest_framework import permissions
from .models import Conversation, Message # Make sure Message is imported

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to:
    - Allow actions on a Conversation object only if the user is a participant.
    - Allow actions on a Message object (view, update, delete) only if the user is a
      participant of the message's conversation.
    - Allow sending (creating) a Message only if the user is a participant
      of the target conversation specified in request.data.
    """
    message_default = "You do not have permission to perform this action."
    message_conversation_required = "Conversation ID must be provided to create a message."
    message_conversation_not_found = "Target conversation does not exist or you are not authorized to access it."
    message_invalid_conversation_id = "Invalid Conversation ID format."

    def has_permission(self, request, view):
        """
        View-level permission check.
        Primarily used for 'create' actions where no object instance exists yet.
        Assumes IsAuthenticated is already checked globally or at view level.
        """
        # Specifically for creating a message in MessageViewSet:
        if view.action == 'create' and hasattr(view, 'basename') and view.basename == 'message':
            conversation_id_str = request.data.get('conversation') # 'conversation' is the field name in MessageSerializer
            
            if not conversation_id_str:
                self.message = self.message_conversation_required
                return False
            
            try:
                # Ensure conversation_id is an integer before querying
                conversation_pk = int(conversation_id_str)
                conversation = Conversation.objects.get(pk=conversation_pk)
                
                # Check if the authenticated user is a participant of this conversation
                if request.user in conversation.participants.all():
                    return True
                else:
                    # User found the conversation but is not a participant
                    self.message = self.message_conversation_not_found
                    return False
            except Conversation.DoesNotExist:
                self.message = self.message_conversation_not_found
                return False
            except (ValueError, TypeError): # Handles non-integer or invalid format for conversation_id
                self.message = self.message_invalid_conversation_id
                return False
        
        # For other actions (list, retrieve, update, delete) or other viewsets,
        # this view-level check passes. Object-level checks are handled by has_object_permission.
        # IsAuthenticated is assumed to be handled by DRF's default settings.
        return True

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.
        Assumes IsAuthenticated is already checked.
        """
        self.message = self.message_default # Reset default message

        if isinstance(obj, Conversation):
            # For Conversation objects, check if the user is a participant
            is_participant = request.user in obj.participants.all()
            if not is_participant:
                self.message = "You are not a participant of this conversation."
            return is_participant
        elif isinstance(obj, Message):
            # For Message objects, check if the user is a participant of the message's conversation
            is_participant = request.user in obj.conversation.participants.all()
            if not is_participant:
                self.message = "You are not a participant of this message's conversation."
            # According to the prompt "Allow only participants in a conversation to send, view, update and delete messages"
            # this means any participant can update/delete any message in that conversation.
            return is_participant
        
        return False # Deny access if object type is not recognized or other conditions