# messaging/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewSet, DeleteUserView, UserConversationHistoryViewSet

router = DefaultRouter()
router.register(r'messages', MessageViewSet, basename='message')
# If DeleteUserView is a ViewSet with actions:
# router.register(r'user-actions', DeleteUserView, basename='user-action')

urlpatterns = [
    path('', include(router.urls)),
    # Custom path for the UserConversationHistoryViewSet's list action
    # This will route GET requests to /api/messaging/conversation-with/<other_user_pk>/
    # to the list method of UserConversationHistoryViewSet.
    path(
        'conversation-with/<int:other_user_pk>/',
        UserConversationHistoryViewSet.as_view({'get': 'list'}),
        name='user-conversation-history'
    ),
    # If DeleteUserView is a simple APIView and not routed by the router:
    # path('user/delete/', DeleteUserView.as_view(), name='delete-user-account'),
]