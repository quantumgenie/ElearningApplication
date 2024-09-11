import factory
from .models import *
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory
from faker import Faker
from django.contrib.auth.hashers import make_password


# model factory classes to use for unit testing
# it is used as template to create table entries for the unit testing

fake = Faker()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.LazyAttribute(lambda _: make_password('password'))

class AppUserFactory(DjangoModelFactory):
    class Meta:
        model = AppUser

    user = factory.SubFactory(UserFactory)
    date_of_birth = factory.Faker('date_of_birth')
    bio = factory.Faker('text', max_nb_chars=200)
    status = factory.Faker('sentence')


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course

    title = factory.Faker('sentence', nb_words=4)
    level = factory.Iterator(['L4', 'L5', 'L6'])
    description = factory.Faker('paragraph')
    creator = factory.SubFactory(UserFactory)
    start_date = factory.Faker('date_this_year')
    end_date = factory.Faker('date_this_year')

class MaterialFactory(DjangoModelFactory):
    class Meta:
        model = Material

    course = factory.SubFactory(CourseFactory)
    creator = factory.SubFactory(UserFactory)
    material_name = factory.Faker('word')
    material_path = factory.django.FileField(filename='dummy.pdf')


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    message = factory.Faker('sentence')
    is_read = factory.Faker('boolean', chance_of_getting_true=50)
    created_at = factory.Faker('date_time_this_year')


class FeedbackFactory(DjangoModelFactory):
    class Meta:
        model = Feedback

    user = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    message = factory.Faker('paragraph')
    sent_at = factory.Faker('date_time_this_year')


class ChatFactory(DjangoModelFactory):
    class Meta:
        model = Chat

    user = factory.SubFactory(UserFactory)
    message = factory.Faker('sentence')
    sent_at = factory.Faker('date_time_this_year')


class EnrollmentFactory(DjangoModelFactory):
    class Meta:
        model = Enrollment

    course = factory.SubFactory(CourseFactory)
    student = factory.SubFactory(UserFactory)
    enrolled_at = factory.Faker('date_time_this_year')
    blocked = factory.Faker('boolean', chance_of_getting_true=10)
