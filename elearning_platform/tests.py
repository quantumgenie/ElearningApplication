import json
from django.test import TestCase, Client
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from django.contrib.auth.models import Group

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from unittest import mock

from django.urls import reverse
from django.urls import reverse_lazy

from .model_factories import *
from .serializers import *

"""
View Tests
"""


class ListNotificationsTest(TestCase):

    def setUp(self):

        # create mock user and log in / course / notification
        self.user = UserFactory()
        self.client.login(username=self.user.username,
                          password='password')
        self.course = CourseFactory()
        NotificationFactory.create_batch(
            2, user=self.user, course=self.course, is_read=False)
        NotificationFactory.create_batch(
            2, user=self.user, course=self.course, is_read=True)

    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse('user_notifications'))
        self.assertRedirects(
            response, f'/login/?next={reverse("user_notifications")}')

    def test_logged_user_can_access(self):
        response = self.client.get(reverse('user_notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'elearning_platform/user_notifications.html')

    def test_contains_correct_notifications(self):
        response = self.client.get(reverse('user_notifications'))
        unread_notifications = response.context['unread_notifications']
        read_notifications = response.context['read_notifications']
        self.assertEqual(unread_notifications.count(), 2)
        self.assertEqual(read_notifications.count(), 2)


class SearchUsersTest(TestCase):

    def setUp(self):

        # creating user and group
        self.user = UserFactory()
        self.group = Group.objects.create(name='teacher')
        self.user.groups.add(self.group)

        # creating client to make request to
        self.create = Client()

    def test_teacher_access(self):
        self.client.login(username=self.user.username,
                          password='password')
        response = self.client.get(reverse('search_users'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'elearning_platform/search_users.html')

    def test__non_teacher_access(self):
        generic_user = UserFactory()
        self.client.login(username=generic_user.username,
                          password='password')
        response = self.client.get(reverse('search_users'))
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_access(self):
        response = self.client.get(reverse('search_users'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f'/login/?next={reverse("search_users")}')


class EnrollToCourseTest(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.group = Group.objects.create(name='student')
        self.user.groups.add(self.group)

        # creating client to make request to
        self.course = CourseFactory()
        self.client = Client()

    def test_get_course_enroll(self):
        self.client.login(username=self.user.username,
                          password='password')
        response = self.client.get(reverse('course_enroll', kwargs={
                                   'course_id': self.course.course_id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'elearning_platform/course/course_enroll.html')

    def test_incorrect_course_id(self):
        self.client.login(username=self.user.username,
                          password='password')
        response = self.client.post(reverse('course_enroll', kwargs={
                                    'course_id': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_success_enroll(self):
        self.client.login(username=self.user.username,
                          password='password')
        response = self.client.post(reverse('course_enroll', kwargs={
                                    'course_id': self.course.course_id}))
        self.assertRedirects(response, reverse(
            'course_detail', kwargs={'pk': self.course.course_id}))
        enrollment = Enrollment.objects.filter(
            course=self.course, student=self.user)
        self.assertTrue(enrollment.exists())

    def test_already_enrolled(self):
        self.client.login(username=self.user.username,
                          password='password')
        Enrollment.objects.create(course=self.course, student=self.user)
        response = self.client.post(reverse('course_enroll', kwargs={
                                    'course_id': self.course.course_id}))
        self.assertEqual(response.status_code, 400)

    def test_redirect_unauthenticated(self):
        response = self.client.post(reverse('course_enroll', kwargs={
                                    'course_id': self.course.course_id}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


"""
API View Tests
"""


class AddCourseAPITest(APITestCase):

    def setUp(self):
        self.user_teacher = UserFactory()
        self.user_student = UserFactory()
        teacher_group = Group.objects.create(name='teacher')
        student_group = Group.objects.create(name='student')
        self.user_teacher.groups.add(teacher_group)
        self.user_student.groups.add(student_group)
        self.url = reverse('api_add_course')

    def test_teacher_add_course(self):
        self.client.login(username=self.user_teacher,
                          password='password')
        course_form_data = factory.build(dict, FACTORY_CLASS=CourseFactory)
        course_form_data['creator'] = self.user_teacher.id
        print(course_form_data)
        response = self.client.post(
            self.url, data=course_form_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(Course.objects.get().title, course_form_data['title'])

    def test_invalid_course_data(self):
        self.client.login(username=self.user_teacher,
                          password='password')
        invalid_course_form_data = {
            'description': 'Not all fields are satisfied in the JSON'
        }
        response = self.client.post(
            self.url, data=invalid_course_form_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)

    def test_student_cannot_add_course(self):
        self.client.login(username=self.user_student,
                          password='password')
        course_form_data = factory.build(dict, FACTORY_CLASS=CourseFactory)
        course_form_data['creator'] = self.user_student.id
        response = self.client.post(
            self.url, data=course_form_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Course.objects.count(), 0)


class DeleteCourseAPITest(APITestCase):

    def setUp(self):

        # adding student and teacher users
        self.user_teacher = UserFactory()
        self.user_student = UserFactory()
        teacher_group = Group.objects.create(name='teacher')
        student_group = Group.objects.create(name='student')
        self.user_teacher.groups.add(teacher_group)
        self.user_student.groups.add(student_group)
        self.course = CourseFactory(creator=self.user_teacher)
        self.url = reverse('api_delete_course', kwargs={'pk': self.course.pk})

    def test_teacher_course_retrieve(self):
        self.client.login(username=self.user_teacher,
                          password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_retrieve_course(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_course_delete(self):
        self.client.login(username=self.user_teacher,
                          password='password')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Course.objects.count(), 0)

    def test_student_cannot_delete_course(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Course.objects.count(), 1)


class DeleteMaterialAPITest(APITestCase):

    def setUp(self):

        # adding student and teacher users
        self.user_teacher = UserFactory()
        self.user_student = UserFactory()
        teacher_group = Group.objects.create(name='teacher')
        student_group = Group.objects.create(name='student')
        self.user_teacher.groups.add(teacher_group)
        self.user_student.groups.add(student_group)

        # adding course/material/mock file
        self.course = CourseFactory(creator=self.user_teacher)
        self.material = MaterialFactory(
            course=self.course, creator=self.user_teacher)
        self.mock_file = SimpleUploadedFile(
            "course_syllabus.txt", b"file_content")

        # adding API url for deleting material
        self.url = reverse('api_delete_material', kwargs={
                           'pk': self.material.pk})

    # adding decorator to alter behaviour of default_storage
    # this allows us to test default_storage without altering any physical files
    @mock.patch('django.core.files.storage.default_storage.delete')
    def test_teacher_can_delete_material(self, mock_delete):
        self.client.login(username=self.user_teacher,
                          password='password')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Material.objects.count(), 0)

        mock_delete.assert_called_once_with(self.material.material_path.path)

    def test_student_cannot_delete_material(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Material.objects.count(), 1)

    def test_unauthenticated_cannot_delete_material(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Material.objects.count(), 1)

    def test_teacher_can_retrieve_material(self):
        self.client.login(username=self.user_teacher,
                          password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['material_id'], self.material.material_id)
        self.assertEqual(
            response.data['material_name'], self.material.material_name)

    def test_student_cannot_retrieve_material(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_retrieve_material(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UnEnrollCOurseAPITest(APITestCase):

    def setUp(self):

        # adding student and teacher users
        self.user_teacher = UserFactory()
        self.user_student = UserFactory()
        self.other_student = UserFactory()
        student_group = Group.objects.create(name='student')
        self.user_student.groups.add(student_group)
        self.other_student.groups.add(student_group)

        # adding course and enrollment
        self.course = CourseFactory(creator=self.user_teacher)
        self.enrollment = EnrollmentFactory(
            course=self.course, student=self.user_student)

        # adding API url for un-enrollment
        self.url = reverse('api_delete_enrollment', kwargs={
                           'pk': self.enrollment.pk})

    def test_student_retrieve_enrollment(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['enrollment_id'], self.enrollment.enrollment_id)

    def test_student_delete_enrollment(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Enrollment.objects.filter(
            pk=self.enrollment.pk).exists())

    def test_unauthorised_cannot_access_enrollment(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorised_cannot_delete_enrollment(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_retrieve_other_student_enrollment(self):

        other_enrollment = EnrollmentFactory(
            course=self.course, student=self.other_student)
        other_url = reverse('api_delete_enrollment', kwargs={
            'pk': other_enrollment.pk})
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_cannot_delete_other_student_enrollment(self):
        other_enrollment = EnrollmentFactory(
            course=self.course, student=self.other_student)
        other_url = reverse('api_delete_enrollment', kwargs={
            'pk': other_enrollment.pk})
        response = self.client.delete(other_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserSearchAPITest(APITestCase):

    def setUp(self):

        # adding student and teacher users
        self.teacher = UserFactory()
        self.second_teacher = UserFactory()
        self.first_student = UserFactory()
        self.second_student = UserFactory()
        teacher_group = Group.objects.create(name='teacher')
        student_group = Group.objects.create(name='student')
        self.teacher.groups.add(teacher_group)
        self.second_teacher.groups.add(teacher_group)
        self.first_student.groups.add(student_group)
        self.second_student.groups.add(student_group)

        # accessing search users url
        self.url = reverse('api_search_users')

    def test_teacher_can_search_users(self):
        self.client.login(username=self.teacher,
                          password='password')
        response = self.client.get(
            self.url, {'query': self.first_student.first_name})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_teacher_can_filter_group(self):
        self.client.login(username=self.teacher,
                          password='password')

        # student search
        response = self.client.get(
            self.url, {'query': self.first_student.first_name, 'group': 'student'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # teacher search
        response = self.client.get(
            self.url, {'query': self.second_teacher.first_name, 'group': 'teacher'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_teacher_search_no_query_data_inserted(self):
        self.client.login(username=self.teacher,
                          password='password')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'No search query provided.')

    def test_unauthorized_user_search(self):
        response = self.client.get(
            self.url, {'query': self.first_student.first_name})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_zero_results_for_non_existent_name(self):
        self.client.login(username=self.teacher,
                          password='password')
        response = self.client.get(
            self.url, {'query': 'NonExistentName'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class RemoveStudentFromCourseAPITest(TestCase):

    def setUp(self):

        # adding student & teacher users
        self.user_teacher = UserFactory()
        self.user_student = UserFactory()
        student_group = Group.objects.create(name='student')
        teacher_group = Group.objects.create(name='teacher')
        self.user_student.groups.add(student_group)
        self.user_teacher.groups.add(teacher_group)

        # adding course and enrollment
        self.course = CourseFactory(creator=self.user_teacher)
        self.enrollment = EnrollmentFactory(
            course=self.course, student=self.user_student)

        # adding API url for un-enrollment
        self.url = reverse('api_remove_student', kwargs={
                           'pk': self.enrollment.pk})

    def test_teacher_remove_student_from_course(self):
        self.client.login(username=self.user_teacher,
                          password='password')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Enrollment.objects.filter(
            pk=self.enrollment.pk).exists())

    def test_unauthorised_cannot_access_student_enrollment(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorised_cannot_remove_student_enrollment(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BlockStudentFromCourseAPITest(APITestCase):

    def setUp(self):

        # adding student & teacher users
        self.user_teacher = UserFactory()
        self.user_student = UserFactory()
        student_group = Group.objects.create(name='student')
        teacher_group = Group.objects.create(name='teacher')
        self.user_student.groups.add(student_group)
        self.user_teacher.groups.add(teacher_group)

        # adding course and enrollment
        self.course = CourseFactory(creator=self.user_teacher)
        self.enrollment = EnrollmentFactory(
            course=self.course, student=self.user_student)

        # adding API url for blocking student
        self.url = reverse('api_block_student', kwargs={
                           'enrollment_id': self.enrollment.enrollment_id})

    def test_teacher_can_block_and_unblock_student(self):
        self.client.login(username=self.user_teacher,
                          password='password')

        # check block
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.enrollment.refresh_from_db()
        self.assertTrue(self.enrollment.blocked)

        # check un-block
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.enrollment.refresh_from_db()
        self.assertFalse(self.enrollment.blocked)

    def test_unauthenticated_cannot_block_student(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_block_with_invalid_enrollment_id(self):
        self.client.login(username=self.user_teacher,
                          password='password')
        invalid_enrollment_url = reverse('api_block_student', kwargs={
            'enrollment_id': 9999})
        response = self.client.post(invalid_enrollment_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MarkNotificationReadAPITest(APITestCase):
    def setUp(self):

        # adding student & teacher users
        self.user_teacher = UserFactory()
        self.user_student = UserFactory()
        student_group = Group.objects.create(name='student')
        teacher_group = Group.objects.create(name='teacher')
        self.user_student.groups.add(student_group)
        self.user_teacher.groups.add(teacher_group)

        # adding course and enrollment
        self.course = CourseFactory(creator=self.user_teacher)
        self.student_read_notification = NotificationFactory(
            user=self.user_student, course=self.course, is_read=True)
        self.student_unread_notifications = NotificationFactory.create_batch(
            2, user=self.user_student, course=self.course, is_read=False)
        self.teacher_read_notification = NotificationFactory(
            user=self.user_teacher, course=self.course, is_read=True)
        self.teacher_unread_notifications = NotificationFactory.create_batch(
            2, user=self.user_teacher, course=self.course, is_read=False)

        # adding API url
        self.url = reverse('user_notifications_read')

    def test_student_mark_as_read(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'],
                         'All notifications marked as read.')

    def test_teachear_mark_as_read(self):
        self.client.login(username=self.user_teacher,
                          password='password')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'],
                         'All notifications marked as read.')

    def test_unauthorized_cannot_mark_as_read(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SendCourseFeedbackAPITest(TestCase):

    def setUp(self):

        # adding student & teacher users
        self.user_teacher = UserFactory()
        self.user_teacher_other = UserFactory()
        self.user_student = UserFactory()
        student_group = Group.objects.create(name='student')
        teacher_group = Group.objects.create(name='teacher')
        self.user_student.groups.add(student_group)
        self.user_teacher.groups.add(teacher_group)
        self.user_teacher_other.groups.add(teacher_group)

        # adding course and enrollment
        self.course = CourseFactory(creator=self.user_teacher)

        # adding feedback json

        # valid
        self.valid_student_feedback = factory.build(
            dict, FACTORY_CLASS=FeedbackFactory)
        self.valid_student_feedback['course'] = self.course.course_id
        self.valid_student_feedback['user'] = self.user_student.id

        # invalid
        self.invalid_student_feedback = factory.build(
            dict, FACTORY_CLASS=FeedbackFactory)
        self.invalid_student_feedback['course'] = self.course.course_id
        self.invalid_student_feedback['user'] = self.user_student.id
        self.invalid_student_feedback['message'] = ''

        # from other teacher
        self.other_teacher_feedback = factory.build(
            dict, FACTORY_CLASS=FeedbackFactory)
        self.other_teacher_feedback['course'] = self.course.course_id
        self.other_teacher_feedback['user'] = self.user_teacher_other.id
        self.other_teacher_feedback['message'] = ''

        # adding API url
        self.url = reverse('api_send_course_feedback')

    def test_student_can_send_feedback(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.post(
            self.url, self.valid_student_feedback, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'],
                         'Feedback submitted successfully.')
        self.assertTrue(Feedback.objects.filter(
            user=self.user_student, course=self.course).exists())

    def test_teacher_cannot_send_feedback(self):
        self.client.login(username=self.user_teacher_other,
                          password='password')
        response = self.client.post(
            self.url, self.other_teacher_feedback, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Feedback.objects.filter(
            user=self.user_student, course=self.course).exists())

    def test_unauthenticated_cannot_send_feedback(self):
        response = self.client.post(
            self.url, self.valid_student_feedback, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Feedback.objects.filter(
            user=self.user_student, course=self.course).exists())

    def test_student_cannot_send_invalid_feedback(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.post(
            self.url, self.invalid_student_feedback, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Feedback.objects.filter(
            user=self.user_student, course=self.course).exists())


class UpdateUserProfileAPITest(APITestCase):

    def setUp(self):

        # adding student & teacher users/appusers
        self.user_teacher = UserFactory()
        self.user_student = UserFactory()
        self.app_user_teacher = AppUserFactory(user=self.user_teacher)
        self.app_user_student = AppUserFactory(user=self.user_student)
        student_group = Group.objects.create(name='student')
        teacher_group = Group.objects.create(name='teacher')
        self.user_student.groups.add(student_group)
        self.user_teacher.groups.add(teacher_group)

        # adding json
        self.valid_user_data = {
            'user': {
                'first_name': 'UpdatedStudentName',
                'last_name': 'UpdatedStudentLastName',
                'email': 'updatedstudent@email.com'
            },
            'app_user': {
                'bio': 'New updated bio'
            }
        }

        # adding API url
        self.url = reverse('user_profile_update')

    def test_student_can_update_profile(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.put(
            self.url, self.valid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'],
                         'User and AppUser updated successfully')
        self.user_student.refresh_from_db()
        self.app_user_student.refresh_from_db()
        self.assertEqual(self.user_student.first_name, 'UpdatedStudentName')
        self.assertEqual(self.user_student.last_name, 'UpdatedStudentLastName')
        self.assertEqual(self.user_student.email, 'updatedstudent@email.com')
        self.assertEqual(self.app_user_student.bio, 'New updated bio')

    def test_teacher_can_update_profile(self):
        self.client.login(username=self.user_teacher,
                          password='password')
        response = self.client.put(
            self.url, self.valid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'],
                         'User and AppUser updated successfully')
        self.user_teacher.refresh_from_db()
        self.app_user_teacher.refresh_from_db()
        self.assertEqual(self.user_teacher.first_name, 'UpdatedStudentName')
        self.assertEqual(self.user_teacher.last_name, 'UpdatedStudentLastName')
        self.assertEqual(self.user_teacher.email, 'updatedstudent@email.com')
        self.assertEqual(self.app_user_teacher.bio, 'New updated bio')

    def test_unauthenticated_cannot_update_profile(self):
        response = self.client.put(
            self.url, self.valid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UpdateUserStatusAPITest(APITestCase):

    def setUp(self):

        # adding student & teacher users/appusers
        self.user_teacher = UserFactory()
        self.user_student = UserFactory()
        self.app_user_teacher = AppUserFactory(user=self.user_teacher)
        self.app_user_student = AppUserFactory(user=self.user_student)
        student_group = Group.objects.create(name='student')
        teacher_group = Group.objects.create(name='teacher')
        self.user_student.groups.add(student_group)
        self.user_teacher.groups.add(teacher_group)

        # adding json
        self.valid_status_data = {
            'status': 'Alive'
        }

        # adding API url
        self.url = reverse('user_status_update')

    def test_student_can_update_status(self):
        self.client.login(username=self.user_student,
                          password='password')
        response = self.client.patch(
            self.url, self.valid_status_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'],
                         'Status updated successfully.')
        self.assertEqual(response.data['status'],
                         'Alive')

    def test_teacher_can_update_status(self):
        self.client.login(username=self.user_teacher,
                          password='password')
        response = self.client.patch(
            self.url, self.valid_status_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'],
                         'Status updated successfully.')
        self.assertEqual(response.data['status'],
                         'Alive')

    def test_unauthenticated_cannot_update_status(self):
        response = self.client.put(
            self.url, self.valid_status_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
