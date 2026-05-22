from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_name = UserSerializer(source='actor', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'link',
            'is_read',
            'actor_name',
            'created_at',
        ]
        read_only_fields = fields

    # def get_actor_name(self, obj):
    #     if obj.actor:
    #         return obj.actor.get_full_name() or obj.actor.username
    #     return None