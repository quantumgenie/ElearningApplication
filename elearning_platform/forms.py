from django import forms
from django.forms import ModelForm
from .models import *
from django.contrib.auth.models import User


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('course', 'creator', 'material_name', 'material_path')


class AddCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'level', 'description', 'start_date', 'end_date')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class UserForm(forms.ModelForm):
    # role field is used to distinguish between students and teachers and add them to their respective restriction Group
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',
                  'email', 'password', 'role')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = AppUser
        fields = ('bio',)
