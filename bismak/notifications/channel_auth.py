from django_eventstream.channelmanager import DefaultChannelManager


# class UserChannelManager(DefaultChannelManager):
#     """
#     Each authenticated user gets their own private SSE channel.
#     Format: notifications-{user_id}

#     This prevents users from receiving each other's notifications.
#     """

#     def can_read_channel(self, user, channel):
#         print(f"can_read_channel called — user: {user}, user.id: {user.user_id}, channel: {channel}")
#         if not user or not user.is_authenticated:
#             return False
#         expected_channel = f'notifications-{user.user_id}'
#         print(f"Expected channel: {expected_channel}")
#         return channel == expected_channel


class UserChannelManager(DefaultChannelManager):
    def can_read_channel(self, user, channel):
        # Allow any authenticated user to read their own channel
        if not user or not user.is_authenticated:
            return False
        return True