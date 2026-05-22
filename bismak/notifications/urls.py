from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/unread-count/', views.unread_count, name='notification-unread-count'),
    path('notifications/mark-all-read/', views.mark_all_read, name='notification-mark-all-read'),
    path('notifications/debug/', views.debug_user, name='notification-debug'),
    path('notifications/<uuid:pk>/read/', views.MarkNotificationReadView.as_view(), name='notification-mark-read'),
]