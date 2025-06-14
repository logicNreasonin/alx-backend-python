# Django-Chat/messaging/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification, MessageHistory # Import MessageHistory

class MessagingSignalTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(username='user1', password='password123')
        cls.user2 = User.objects.create_user(username='user2', password='password123')
        cls.user3 = User.objects.create_user(username='user3', password='password123')

    # ... (previous tests for notifications remain here) ...

    def test_notification_created_on_new_message(self):
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 0)
        message_content = "Hello User2, this is a test message!"
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content=message_content
        )
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 1)
        notification = Notification.objects.get(user=self.user2)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.text, f"You have a new message from {self.user1.username}.")
        self.assertFalse(notification.is_read)

    def test_no_notification_on_message_update(self):
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Initial message"
        )
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), 1)
        initial_notification_count = Notification.objects.filter(user=self.user2).count()
        message.is_read = True
        message.save()
        self.assertEqual(Notification.objects.filter(user=self.user2).count(), initial_notification_count)

    # New tests for message edit history

    def test_new_message_not_marked_edited_and_no_history(self):
        """Test that a newly created message is not marked as edited and has no history."""
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="A brand new message."
        )
        self.assertFalse(message.edited)
        self.assertEqual(message.edit_history.count(), 0)

    def test_message_edit_logs_history_and_sets_edited_flag(self):
        """
        Test that editing a message's content logs its old content to MessageHistory
        and sets the 'edited' flag on the Message.
        """
        original_content = "This is the original content."
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content=original_content
        )
        self.assertFalse(message.edited) # Initially not edited
        self.assertEqual(MessageHistory.objects.filter(message=message).count(), 0)

        # Edit the message content
        new_content = "This is the updated, edited content."
        message.content = new_content
        message.save()

        # Refresh message from DB to ensure 'edited' flag is correctly fetched
        message.refresh_from_db()

        self.assertTrue(message.edited) # Should now be marked as edited
        self.assertEqual(MessageHistory.objects.filter(message=message).count(), 1)
        
        history_entry = MessageHistory.objects.get(message=message)
        self.assertEqual(history_entry.old_content, original_content)
        self.assertEqual(history_entry.message, message) # Redundant check, but good for clarity

        # Edit again
        very_new_content = "Edited yet again!"
        message.content = very_new_content
        message.save()

        message.refresh_from_db()
        self.assertTrue(message.edited) # Still marked as edited
        self.assertEqual(MessageHistory.objects.filter(message=message).count(), 2)

        latest_history_entry = MessageHistory.objects.filter(message=message).latest('edited_at')
        self.assertEqual(latest_history_entry.old_content, new_content)


    def test_message_update_no_content_change_no_history(self):
        """
        Test that updating a message without changing its content
        does not create a history entry or change the 'edited' status unnecessarily.
        """
        original_content = "Content that will not change."
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content=original_content,
            is_read=False
        )
        self.assertFalse(message.edited)
        initial_history_count = MessageHistory.objects.filter(message=message).count() # Should be 0

        # Update a non-content field (e.g., is_read)
        message.is_read = True
        message.save()

        message.refresh_from_db()

        # The 'edited' flag should remain False if it wasn't True before,
        # because the content itself didn't change.
        self.assertFalse(message.edited)
        self.assertEqual(MessageHistory.objects.filter(message=message).count(), initial_history_count)

    def test_message_update_no_content_change_preserves_edited_flag(self):
        """
        Test that if a message was already edited, updating a non-content field
        does not clear the 'edited' flag or add new history for content.
        """
        message = Message.objects.create(sender=self.user1, receiver=self.user2, content="Original")
        
        # First edit (content change)
        message.content = "First Edit"
        message.save()
        message.refresh_from_db()
        self.assertTrue(message.edited)
        self.assertEqual(message.edit_history.count(), 1)

        # Now update a non-content field
        message.is_read = True
        message.save()
        message.refresh_from_db()

        self.assertTrue(message.edited) # Edited flag should persist
        self.assertEqual(message.edit_history.count(), 1) # No new history entry for this non-content change