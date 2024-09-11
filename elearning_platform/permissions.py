from rest_framework.permissions import BasePermission
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

"""
Custom permissions
"""
# checking if the user is a teacher


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='teacher').exists()

# checking if the user is a student


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name='student').exists()


# checking if the logged user is the creator


class IsCreator(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.creator == request.user


"""
Custom permission decorators
"""

# require user to be authenticated and in a certain group


def group_required(*group_names):
    def decorator(view_function):
        def _wrapped_view(request, *args, **kwargs):
            # redirect to login if not authenticated
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.groups.filter(name__in=group_names).exists():
                return view_function(request, *args, **kwargs)
            # redirect to main page if not in group
            # return redirect('index')
            raise PermissionDenied
        return _wrapped_view
    return decorator
