from .models import *
from .serializers import *
from elearning_platform.permissions import *
from django.core.files.storage import default_storage
from rest_framework import status, mixins, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q


# teacher: add new course


class AddCourseAPI(mixins.CreateModelMixin,
                   generics.GenericAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def post(self, request, *args, **kwargs):
        # checking if user is a 'teacher'
        if not request.user.groups.filter(name='teacher').exists():
            return Response({"detail": "You are not authorized to add courses."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # saving serializer while adding creator field
            serializer.save(creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# teacher: delete course


class DeleteCourseAPI(mixins.RetrieveModelMixin,
                      mixins.DestroyModelMixin,
                      generics.GenericAPIView):
    # check the user is logged and has enrollmentId
    permission_classes = [IsAuthenticated, IsTeacher, IsCreator]
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

# teacher: delete uploaded course material


class DeleteMaterialAPI(mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    # check the user is logged and has enrollmentId
    permission_classes = [IsAuthenticated, IsTeacher, IsCreator]
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        material = self.get_object()
        material_path = material.material_path.path
        if default_storage.exists(material_path):
            default_storage.delete(material_path)

        return self.destroy(request, *args, **kwargs)


class UnEnrollCourseAPI(mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    # check the user is logged in and is student
    permission_classes = [IsAuthenticated, IsStudent]
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

# teacher: search key word in the users db


class UserSearchAPI(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query', None)
        group_filter = request.query_params.get('group', None)
        if query:
            # filter users based on key word and only in 'student'  and 'teacher' groups
            matching_users = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query),
                groups__name__in=['student', 'teacher']
            ).distinct()
            # applying group filter
            if group_filter in ['student', 'teacher']:
                matching_users = matching_users.filter(
                    groups__name=group_filter)
            # collect list of user matching search and return it as a response
            users_data = [
                {
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "id": user.id,
                    "group": user.groups.values_list('name', flat=True).first()
                } for user in matching_users
            ]
            return Response(users_data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No search query provided."}, status=status.HTTP_400_BAD_REQUEST)

# teacher: remove student from course


class RemoveStudentFromCourseAPI(mixins.RetrieveModelMixin,
                                 mixins.DestroyModelMixin,
                                 generics.GenericAPIView):
    # check the user is logged and has enrollmentId
    permission_classes = [IsAuthenticated, IsTeacher]
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


# teacher: block student from course

class BlockStudentFromCourseAPI(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def post(self, request, enrollment_id):
        # Get the specific enrollment object
        enrollment = get_object_or_404(Enrollment, enrollment_id=enrollment_id)

        # Mark the student as blocked
        enrollment.blocked = not enrollment.blocked
        enrollment.save()

        # Return a success response
        if enrollment.blocked:
            return Response({"detail": "Student blocked successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Student un-blocked successfully."}, status=status.HTTP_200_OK)


# student & teacher: mark all notifications as read
class MarkNotificationsRead(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Update all unread notifications for the user to is_read=True
        notifications = Notification.objects.filter(
            user=request.user, is_read=False)
        notifications.update(is_read=True)

        return Response({'message': 'All notifications marked as read.'}, status=200)

# student: send course feedback


class SendCourseFeedbackAPI(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, *args, **kwargs):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({'message': 'Feedback submitted successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# student & teacher: update user profile


class UpdateUserProfileAPI(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        app_user = AppUser.objects.get(user=user)
        user_data = request.data.get('user')
        app_user_data = request.data.get('app_user')

        # update User fields
        user_serializer = UserSerializer(
            user, data=user_data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # update AppUser fields
        app_user_serializer = AppUserSerializer(
            app_user, data=app_user_data, partial=True)
        if app_user_serializer.is_valid():
            app_user_serializer.save()
        else:
            return Response(app_user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'User and AppUser updated successfully'}, status=status.HTTP_200_OK)

# student & teacher: update user status


class UpdateUserStatusAPI(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        try:
            # get instance of authenticated user
            app_user = AppUser.objects.get(user=request.user)
        except AppUser.DoesNotExist:
            return Response({"error": "AppUser not found."}, status=status.HTTP_404_NOT_FOUND)

        # deserialize & validate the data
        serializer = AppUserStatusSerializer(
            app_user, data=request.data, partial=True)

        if serializer.is_valid():
            # save status change
            serializer.save()
            return Response({"message": "Status updated successfully.", "status": serializer.data['status']}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
