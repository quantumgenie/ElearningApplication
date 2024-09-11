from .models import Material, Notification, Enrollment
from django.dispatch import receiver
from django.db.models.signals import post_save
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# inserting notification in db for each course material added by the teacher


@receiver(post_save, sender=Material)
def insert_material_notification(sender, instance, created, **kwargs):
    if created:
        # searching for all students enrolled in the course
        enrollments = Enrollment.objects.filter(
            course=instance.course, blocked=False)
        # inserting notification for each student enrolled
        for enrollment in enrollments:
            notification = Notification.objects.create(
                user=enrollment.student,
                course=instance.course,
                message=f"'{instance.material_name}' added to the course '{
                    instance.course.title}'.",
                is_read=False
            )
            # send notification through WebSocket
            send_ws_notification(notification)

# inserting notification in db for each student enrollment


@receiver(post_save, sender=Enrollment)
def insert_enrollment_notification(sender, instance, created, **kwargs):
    if created:
        # inserting notification for the course creator
        notification = Notification.objects.create(
            user=instance.course.creator,
            course=instance.course,
            message=f"'{instance.student.first_name} {
                instance.student.last_name}' has enrolled in '{instance.course.title}'.",
            is_read=False
        )
        # send notification through WebSocket
        send_ws_notification(notification)

# sending WebSocket notificaiton
# this is used for live


def send_ws_notification(notification):
    channel_layer = get_channel_layer()
    group_name = f'notifications_{notification.user.id}'
    unread_count = Notification.objects.filter(
        user=notification.user, is_read=False).count()
    try:
        print(f"SIGNALS: Sending message to group {
              group_name}: {notification.message}")
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification',
                'message': notification.message,
                'unread_count': unread_count,
            }
        )
    except Exception as e:
        print(f"Error in send_ws_notification: {e}")
