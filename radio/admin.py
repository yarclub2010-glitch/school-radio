from django.contrib import admin

from .models import BreakSlot, Track


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'uploaded_by', 'school_class', 'status', 'plays', 'created_at']
    list_filter = ['status', 'school_class']
    search_fields = ['title', 'artist', 'uploaded_by']
    actions = ['approve', 'reject']

    @admin.action(description='Одобрить выбранные')
    def approve(self, request, queryset):
        queryset.update(status=Track.Status.APPROVED)

    @admin.action(description='Отклонить выбранные')
    def reject(self, request, queryset):
        queryset.update(status=Track.Status.REJECTED)


@admin.register(BreakSlot)
class BreakSlotAdmin(admin.ModelAdmin):
    list_display = ['name', 'start', 'end', 'weekdays']


admin.site.site_header = 'Школьное радио — управление'
