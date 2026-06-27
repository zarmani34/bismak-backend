from django_eventstream.channelmanager import DefaultChannelManager

class UserChannelManager(DefaultChannelManager):
    def can_read_channel(self, user, channel):
        # Allow any authenticated user to read their own channel
        if not user or not user.is_authenticated:
            return False
        return True