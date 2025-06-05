# messaging_app/chats/permissions.py

from rest_framework import permissions
from .models import Conversation, Message # Ensure Message is imported if type checking specific messages

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to:
    - Allow actions on a Conversation object only if the user is a participant.
    - For views nested under a conversation (e.g., MessageViewSet):
        - Allow list/create actions only if the user is a participant of the parent conversation (from URL kwargs).
    - For Message objects (retrieve, update, delete):
        - Allow actions only if the user is a participant of the message's conversation.
    """
    message_default = "You do not have permission to perform this action."
    message_auth_required = "Authentication credentials were not provided or are invalid."
    message_conversation_not_found_url = "The conversation specified in the URL does not exist or you are not authorized."
    message_conversation_not_found_data = "The conversation specified in the request data does not exist or you are not authorized."
    message_invalid_conversation_id_url = "Invalid Conversation ID format in URL."
    message_invalid_conversation_id_data = "Invalid Conversation ID format in request data."
    message_conversation_required_data = "Conversation ID must be provided in request data for this action."

    def has_permission(self, request, view):
        """
        View-level permission check.
        Primarily used for 'list' and 'create' actions where no object instance exists yet.
        """
        if not request.user or not request.user.is_authenticated:
            self.message = self.message_auth_required
            return False

        # Prioritize 'conversation_pk' from URL kwargs for nested views (e.g., MessageViewSet)
        # This 'conversation_pk' comes from the 'lookup' field in NestedDefaultRouter.
        # Assumes your Conversation model's PK is 'conversation_id' (UUID).
        conversation_pk_from_url = view.kwargs.get('conversation_pk')

        if conversation_pk_from_url:
            try:
                # Conversation.pk is 'conversation_id' and is a UUID.
                # Django's ORM can handle string UUIDs for pk lookups.
                conversation = Conversation.objects.get(pk=conversation_pk_from_url)
                
                if request.user in conversation.participants.all():
                    return True # User is a participant of the conversation from URL, allow.
                else:
                    self.message = self.message_conversation_not_found_url # More specific message
                    return False
            except Conversation.DoesNotExist:
                self.message = self.message_conversation_not_found_url
                return False
            except (ValueError, TypeError): # Handles invalid UUID format from URL if conversion/validation happens
                self.message = self.message_invalid_conversation_id_url
                return False
        
        # Fallback: If not a nested route identified by 'conversation_pk' in URL kwargs,
        # AND it's a 'create' action for a view identified by basenames 'message' or 'conversation-messages'
        # (e.g., a non-nested message creation endpoint), check 'conversation' from request.data.
        # Your MessageViewSet's nested registration uses basename 'conversation-messages'.
        # A non-nested one might use 'message'.
        elif view.action == 'create' and hasattr(view, 'basename') and view.basename in ['message', 'conversation-messages']:
            conversation_id_from_data = request.data.get('conversation')
            
            if not conversation_id_from_data:
                self.message = self.message_conversation_required_data
                return False
            
            try:
                conversation = Conversation.objects.get(pk=conversation_id_from_data)
                if request.user in conversation.participants.all():
                    return True
                else:
                    self.message = self.message_conversation_not_found_data
                    return False
            except Conversation.DoesNotExist:
                self.message = self.message_conversation_not_found_data
                return False
            except (ValueError, TypeError): 
                self.message = self.message_invalid_conversation_id_data
                return False
        
        # For other cases (e.g., ConversationViewSet list/create, or if above checks pass),
        # allow and let object-level permissions handle instance-specific checks.
        return True

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.
        """
        if not request.user or not request.user.is_authenticated: # Should be caught by has_permission ideally
            self.message = self.message_auth_required
            return False

        self.message = self.message_default # Reset default message

        if isinstance(obj, Conversation):
            is_participant = request.user in obj.participants.all()
            if not is_participant:
                self.message = "You are not a participant of this conversation."
            return is_participant
        elif isinstance(obj, Message):
            # For Message objects, check if the user is a participant of the message's conversation
            is_participant = request.user in obj.conversation.participants.all()
            if not is_participant:
                self.message = "You are not a participant of this message's conversation."
            return is_participant
        
        return False