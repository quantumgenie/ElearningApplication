from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User

# Serializer models - for converting complex data types into python data types that would be rendered to JSON,XML, etc.


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class AppUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ['date_of_birth', 'bio', 'status']


class AppUserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ['status']


class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = [
            'course_id',
            'title',
            'level',
            'description',
            'start_date',
            'end_date',
            'creator',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['course_id', 'creator', 'created_at', 'updated_at']

    def create(self, validated_data):
        course = Course(**{**validated_data})
        course.save()
        return course


class MaterialSerializer(serializers.ModelSerializer):

    class Meta:
        model = Material
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = '__all__'


class FeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback
        fields = ['course', 'message']


class ChatSerializer(serializers.ModelSerializer):

    class Meta:
        model = Chat
        fields = '__all__'


class EnrollmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Enrollment
        fields = '__all__'

    def create(self, validated_data):
        enrollment = Enrollment(**{**validated_data})
        enrollment.save()
        return enrollment
