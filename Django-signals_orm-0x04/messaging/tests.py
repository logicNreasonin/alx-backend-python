# messaging/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification

class MessagingSignalTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create users for testing
        cls.user1 = User.objects.create_user(username='user1', password='password123')
        cls.user2 = User.objects.create_user(username='user2', password='password123')
        cls.user3 = User.objects.create_user(username='user3', password='password123')

    def test_notification_created_on_new_message(self):
        """
        Test that a Notification is automatically created when a new Message is saved.
        """
        # Ensure no notifications exist initially for user2
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 0)

        # User1 sends a message to User2
        message_content = "Hello User2, this is a test message!"
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content=message_content
        )

        # Check if a notification was created for user2
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 1)
        
        notification = Notification.objects.get(user=self.user2)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.text, f"You have a new message from {self.user1.username}.")
        self.assertFalse(notification.is_read)

    def test_no_notification_on_message_update(self):
        """
        Test that a Notification is NOT created when an existing Message is updated.
        """
        # User1 sends a message to User2
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Initial message"
        )
        # At this point, one notification should exist for user2
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 1)
        initial_notification_count = Notification.objects.filter(user=self.user2).count()

        # Update the message (e.g., mark as read or change content)
        message.is_read = True
        message.content = "Updated content"
        message.save()

        # Check that NO new notification was created for user2
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), initial_notification_count)

    def test_multiple_messages_create_multiple_notifications(self):
        """
        Test that multiple new messages to the same user create multiple notifications.
        """
        Message.objects.create(sender=self.user1, receiver=self.user2, content="Message 1")
        Message.objects.create(sender=self.user3, receiver=self.user2, content="Message 2 from user3")

        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 2)
        notifications = Notification.objects.filter(user=self.user2).order_by('created_at')
        
        self.assertTrue(f"from {self.user1.username}" in notifications[0].text)
        self.assertTrue(f"from {self.user3.username}" in notifications[1].text)

    def test_notification_for_correct_receiver(self):
        """
        Test that notification is created for the correct receiver, not sender or other users.
        """
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="A message for user2"
        )

        # Notification should be for user2
        self.assertTrue(Notification.objects.filter(user=self.user2).exists())
        # No notification for user1 (sender)
        self.assertFalse(Notification.objects.filter(user=self.user1).exists())
        # No notification for user3 (unrelated user)
        self.assertFalse(Notification.objects.filter(user=self.user3).exists())