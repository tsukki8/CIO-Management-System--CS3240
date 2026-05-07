from django.contrib import admin
from .models import Profile, CIO

class ProfileAdmin(admin.ModelAdmin):
    """
    Custom admin for Profile with enhanced display.
    Users can be promoted to admin role here (this is intentional - 
    admin interface requires superuser access already).
    The web application prevents admins from assigning the admin role,
    but Django admin allows full management including removal.
    """
    list_display = ['user', 'role', 'get_profile_picture']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['user']
    
    def get_profile_picture(self, obj):
        return "Yes" if obj.profile_picture else "No"
    get_profile_picture.short_description = 'Has Profile Picture'

admin.site.register(Profile, ProfileAdmin)
admin.site.register(CIO)
