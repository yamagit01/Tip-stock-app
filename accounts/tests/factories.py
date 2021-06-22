from django.contrib.auth import get_user_model
from factory import Faker, LazyAttribute, PostGenerationMethodCall, Sequence
from factory.django import DjangoModelFactory, ImageField
from faker import Faker

UserModel = get_user_model()
fake_ja = Faker('ja_JP')
Faker.seed(0)

class UserFactory(DjangoModelFactory):
    class Meta:
        model = UserModel
        django_get_or_create = ('username','email')

    username = Sequence(lambda n: f'user{n}')
    email = LazyAttribute(lambda o: f'{o.username}@example.com')
    password = PostGenerationMethodCall('set_password', 'test')
    icon = ImageField(filename="test.jpg")
