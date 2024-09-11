from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class AppUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username


class Course(models.Model):
    LEVEL_CHOICES = [
        ('L4', 'Level 4'),
        ('L5', 'Level 5'),
        ('L6', 'Level 6'),
    ]
    course_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'pk': self.course_id})

    def __str__(self):
        return self.title


class Material(models.Model):
    material_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='materials')
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='materials')
    material_name = models.CharField(max_length=255)
    material_path = models.FileField(upload_to='materials/')
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.material_name


class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications')
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.user.email} on {self.course.title}'


class Feedback(models.Model):
    feedback_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='feedbacks')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback by {self.user.email} for {self.course.title}'


class Chat(models.Model):
    message_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='chats')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Chat message by {self.user.email}'


class Enrollment(models.Model):
    enrollment_id = models.AutoField(primary_key=True)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    blocked = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.student.email} enrolled in {self.course.title}'
