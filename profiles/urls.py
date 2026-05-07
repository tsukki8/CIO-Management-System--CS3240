# AI Citation
# Description: Profiles app URL routes
# AI Use: Generated with GitHub Copilot on 2026-03-29.
#   Prompt: "Create routes for dashboards, CIO settings, events, and membership approval"
# Notes: Multi-CIO selection, membership approval/rejection, event management

# AI Citation
# Description: New routes for CIO calendar and event promotion
# AI Use: Generated with GitHub Copilot on 2026-04-16.
#   Prompt: "Add URL patterns for centralized CIO calendar view and event promotion endpoint"
# Notes: Routes added: /exec/calendar/ for CIO calendar and /cio/<id>/event/<id>/promote/ for event promotion action.

from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('admin-dashboard/', views.user_admin_dashboard, name='user_admin_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.profile_view, name='profile'),
    path('member/', views.member_view, name='member'),
    path('exec/', views.exec_view, name='exec'),
    path('exec/calendar/', views.cio_calendar_view, name='cio_calendar'),

    path('chat/', views.inbox_view, name='inbox'),
    path('chat/start/<int:user_id>/', views.start_chat_view, name='start_chat'),

    path('membership/<int:membership_id>/approve/', views.approve_membership, name='approve_membership'),
    path('membership/<int:membership_id>/reject/', views.reject_membership, name='reject_membership'),
    path('cio/request/', views.request_cio_role, name='request_cio_role'),
    path('cio-request/<int:cio_request_id>/', views.cio_request_detail, name='cio_request_detail'),
    path('cio-request/<int:cio_request_id>/approve/', views.approve_cio_request, name='approve_cio_request'),
    path('cio-request/<int:cio_request_id>/reject/', views.reject_cio_request, name='reject_cio_request'),
    path('cio/create/', views.create_cio, name='create_cio'),
    path('cio/settings/', views.cio_settings_redirect, name='cio_settings_redirect'),
    path('cio/<int:cio_id>/settings/', views.cio_settings_view, name='cio_settings'),
    path('cio/<int:cio_id>/', views.cio_detail, name='cio_detail'),
    path('cio/<int:cio_id>/join/', views.request_join, name='request_join'),
    path("cio/<int:cio_id>/create_event/", views.create_event, name="create_event"),
    path('cio/<int:cio_id>/event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('cio/<int:cio_id>/event/<int:event_id>/promote/', views.promote_event_view, name='promote_event'),
    path("cio/<int:cio_id>/event/<int:event_id>/", views.event_detail, name="event_detail"),
    path("cio/<int:cio_id>/event/<int:event_id>/rsvp/", views.rsvp_event, name="rsvp_event"),
    path('calendar/', views.calendar_view, name='calendar'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notification_id>/open/', views.open_notification_view, name='open_notification'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]