# messaging/admin.py
from django.contrib import admin
from .models import Message, Notification

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read', 'sender', 'receiver')
    search_fields = ('content', 'sender__username', 'receiver__username')
    readonly_fields = ('timestamp',)

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
            return f"Msg from {obj.message.sender.username} to {obj.message.receiver.username}"
        return "N/A"
    message_summary.short_description = 'Related Message'