# Django-Chat/messaging/admin.py
from django.contrib import admin
from .models import Message, Notification, MessageHistory # Import MessageHistory

class MessageHistoryInline(admin.TabularInline): # Or admin.StackedInline
    model = MessageHistory
    extra = 0 # Show no empty forms for new history by default
    readonly_fields = ('old_content', 'edited_at')
    can_delete = False # Usually, history should not be deletable from here
    ordering = ('-edited_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content_preview', 'timestamp', 'is_read', 'edited') # Add 'edited'
    list_filter = ('timestamp', 'is_read', 'edited', 'sender', 'receiver') # Add 'edited'
    search_fields = ('content', 'sender__username', 'receiver__username')
    readonly_fields = ('timestamp',)
    inlines = [MessageHistoryInline] # Add the inline here

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message_summary', 'text_preview', 'created_at', 'is_read')
    list_filter = ('created_at', 'is_read', 'user')
    search_fields = ('text', 'user__username', 'message__content')
    readonly_fields = ('created_at',)

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text Preview'

    def message_summary(self, obj):
        if obj.message:
            return f"Msg ID {obj.message.pk} from {obj.message.sender.username}"
        return "N/A"
    message_summary.short_description = 'Related Message'


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    list_display = ('message_summary', 'old_content_preview', 'edited_at')
    list_filter = ('edited_at', 'message__sender', 'message__receiver')
    search_fields = ('old_content', 'message__content')
    readonly_fields = ('message', 'old_content', 'edited_at')

    def old_content_preview(self, obj):
        return obj.old_content[:70] + '...' if len(obj.old_content) > 70 else obj.old_content
    old_content_preview.short_description = 'Old Content'

    def message_summary(self, obj):
        return f"Original Msg ID {obj.message.pk} (Sender: {obj.message.sender.username})"
    message_summary.short_description = 'Original Message'