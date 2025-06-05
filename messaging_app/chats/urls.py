# messaging_app/chats/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter # Import NestedDefaultRouter
from .views import ConversationViewSet, MessageViewSet

# Create a top-level router for conversations
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')

# Create a nested router for messages within a specific conversation.
# - The first argument is the parent router (router).
# - The second argument is the URL prefix of the parent resource (r'conversations').
# - The third argument `lookup` is the name of the URL keyword argument that will capture
#   the parent's primary key. We'll use 'conversation_pk'.
# This means that MessageViewSet will receive self.kwargs['conversation_pk'].
conversations_messages_router = NestedDefaultRouter(router, r'conversations', lookup='conversation_pk')
conversations_messages_router.register(
    r'messages', # This will create URLs like /conversations/<conversation_pk>/messages/
    MessageViewSet,
    basename='conversation-messages' # A unique basename for the nested routes
)

# The API URLs now include both the top-level conversation routes
# and the nested message routes.
urlpatterns = [
    path('', include(router.urls)), # For /conversations/ and /conversations/<conversation_pk>/
    path('', include(conversations_messages_router.urls)), # For /conversations/<conversation_pk>/messages/ etc.
]