from .models import *
from .forms import *
from .permissions import group_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import Group
from django.views.generic import ListView, TemplateView, UpdateView, DetailView
from django.views import View


# student & teacher: list notifications


@method_decorator(login_required, name='dispatch')
class ListNotifications(TemplateView):
    template_name = 'elearning_platform/user_notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get user's notifications
        notifications = Notification.objects.filter(
            user=self.request.user).order_by('-is_read', '-created_at')
        context['unread_notifications'] = notifications.filter(is_read=False)
        context['read_notifications'] = notifications.filter(is_read=True)
        return context

# teacher: search users page


@method_decorator(login_required, name='dispatch')
@method_decorator(group_required('teacher'), name='dispatch')
class SearchUsersView(View):
    template_name = 'elearning_platform/search_users.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

# student: enroll to course:


@method_decorator(login_required, name='dispatch')
@method_decorator(group_required('student'), name='dispatch')
class EnrollToCourse(View):

    def post(self, request, course_id):
        # capture previous URL
        course = get_object_or_404(Course, course_id=course_id)
        # check if student already enrolled
        if Enrollment.objects.filter(course=course, student=request.user).exists():
            return HttpResponse("You are already enrolled in this course.", status=400)
        # create the enrollment
        Enrollment.objects.create(course=course, student=request.user)
        # redirect or return success message
        return redirect('course_detail', pk=course.course_id)

    def get(self, request, course_id):
        course = get_object_or_404(Course, course_id=course_id)
        return render(request, 'elearning_platform/course/course_enroll.html', {'course': course})

# teacher: view user details


@method_decorator(login_required, name='dispatch')
# @method_decorator(group_required('teacher'), name='dispatch')
class UserDetail(DetailView):
    model = User
    context_object_name = 'user_detail'
    template_name = 'elearning_platform/user_profile.html'

    def get_object(self, queryset=None):
        user_id = self.kwargs.get('pk')
        return get_object_or_404(User, id=user_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        appUser = AppUser.objects.get(user=user)
        context['app_user'] = appUser
        if user.groups.filter(name='student').exists():
            # if user is a student get enrolled courses
            enrolled_courses = Course.objects.filter(enrollments__student=user)
            context['enrolled_courses'] = enrolled_courses
            context['is_student'] = True
            context['is_teacher'] = False
        elif user.groups.filter(name='teacher').exists():
            # if user is a teacher get created courses
            created_courses = Course.objects.filter(creator=user)
            context['created_courses'] = created_courses
            context['is_teacher'] = True
            context['is_student'] = False

        return context


# teacher: upload course material


@login_required
@group_required('teacher')
def upload_material(request):
    # retrieve course id and user
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        # retrieve material
        material_to_upload = request.FILES.get('myfile')
        if course_id and material_to_upload:
            course = get_object_or_404(Course, course_id=course_id)
            user = request.user
            # create + save material object
            material = Material.objects.create(
                course=course,
                creator=user,
                material_name=material_to_upload.name,
                material_path=material_to_upload
            )
            material.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponseRedirect('/')

# teacher:  edit course


class CourseEdit(UpdateView):
    model = Course
    fields = ['title', 'level', 'description', 'start_date', 'end_date']
    template_name = 'elearning_platform/course/course_edit.html'

    def get_success_url(self):
        # redirect to course after update
        return reverse_lazy('course_detail', kwargs={'pk': self.object.pk})

# teacher: go to search users page


@login_required
@group_required('teacher')
def search_users(request):
    return render(request, 'elearning_platform/search_users.html')


# student and teacher: view course details and name of the creator
@method_decorator(login_required, name='dispatch')
class CourseDetail(DetailView):
    model = Course
    context_object_name = 'course'
    template_name = 'elearning_platform/course/course_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = context['course']
        context['creator_name'] = f"{course.creator.first_name} {
            course.creator.last_name}"
        context['materials'] = course.materials.all()
        enrollments = Enrollment.objects.filter(course=course)
        context['enrollments'] = enrollments
        feedbacks = Feedback.objects.filter(course=course).order_by('-sent_at')
        context['feedbacks'] = feedbacks
        is_enrolled = enrollments.filter(student=self.request.user).exists()
        context['is_enrolled'] = is_enrolled
        return context

# student and teacher: list courses


@method_decorator(login_required, name='dispatch')
class ListCourses(TemplateView):
    template_name = 'elearning_platform/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # full info of the logged user
        context['app_user'] = AppUser.objects.get(
            user=user)
        # courses created by logged teacher
        context['created_courses'] = Course.objects.filter(
            creator=user)
        # courses not created by logged teacher
        context['other_teachers_courses'] = Course.objects.exclude(
            creator=user)
        # courses student is enrolled in
        context['enrolled_courses'] = Enrollment.objects.filter(
            student=user)

        # courses student is not enrolled in
        context['not_enrolled_courses'] = Course.objects.exclude(
            enrollments__student=user)
        return context

# teacher: add new course


@login_required
@group_required('teacher')
def add_course_view(request):
    return render(request, 'elearning_platform/course/add_course_api.html')

# student: view more courses


@method_decorator(login_required, name='dispatch')
@method_decorator(group_required('student'), name='dispatch')
class ListStudentMoreCourses(ListView):
    model = Course
    template_name = 'elearning_platform/more_courses.html'
    context_object_name = 'courses'

    def get_queryset(self):
        return Course.objects.exclude(enrollments__student=self.request.user)

# view live chat


@login_required
@group_required('student', 'teacher')
def live_chat(request):
    return render(request, 'elearning_platform/chat/live_chat.html')

# view live chat room


@login_required
@group_required('student', 'teacher')
def live_chat_room(request, room_name):
    print(f"Room Name: {room_name}")
    # determining what group the user is part of
    user_group = None
    if request.user.groups.filter(name='student').exists():
        user_group = 'student'
    elif request.user.groups.filter(name='teacher').exists():
        user_group = 'teacher'
    # adding room name, current user and the the user's access group to context
    context = {
        'room_name': room_name,
        'user': request.user,
        'user_group': user_group,
    }
    return render(request, 'elearning_platform/chat/live_chat_room.html', context)

# log out the user and redirect to main page


@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('../')

# log in the user & let user know if the account is disabled or login is invalid


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('../')
            else:
                return HttpResponse('Your account is disabled')
        else:
            return HttpResponse('Invalid login')
    else:
        return render(request, 'elearning_platform/login.html')

# register the user & add the user to designated group: student / teacher


def register(request):
    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)
        if user_form.is_valid and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            if 'bio' is user_form.cleaned_data:
                profile.bio = request.DATA['bio']
            profile.save()
            # add user to its designated restrictions Group (student/teacher)
            role = user_form.cleaned_data['role']
            if role == 'student':
                group = Group.objects.get(name='student')
            elif role == 'teacher':
                group = Group.objects.get(name='teacher')
            user.groups.add(group)
            registered = True
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
    return render(request, 'elearning_platform/register.html', {'user_form': user_form, 'profile_form': profile_form, 'registered': registered})


def index(request):
    return render(request, 'elearning_platform/index.html')
