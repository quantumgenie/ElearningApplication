from django.contrib import admin
from .models import *

# Admin models - For viewing/manipulating DB in admin mode


class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'course_id',
        'title',
        'level',
        'description',
        'creator',
        'created_at',
        'updated_at',
        'start_date',
        'end_date',
    )


class MaterialAdmin(admin.ModelAdmin):
    list_display = (
        'material_id',
        'course',
        'creator',
        'material_name',
        'material_path',
        'added_at',
    )


class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'notification_id',
        'user',
        'course',
        'message',
        'is_read',
        'created_at',
    )


class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'feedback_id',
        'course',
        'user',
        'message',
        'sent_at',
    )


class ChatAdmin(admin.ModelAdmin):
    list_display = (
        'message_id',
        'user',
        'message',
        'sent_at',
    )


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'enrollment_id',
        'course',
        'student',
        'enrolled_at',
        'blocked',
    )


admin.site.register(AppUser)
admin.site.register(Course, CourseAdmin)
admin.site.register(Material, MaterialAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
