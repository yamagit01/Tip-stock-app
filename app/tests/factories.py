import datetime

from accounts.tests.factories import UserFactory
from app.models import Code, Comment, Like, Notification, Tip
from django.contrib.auth import get_user_model
from factory import Faker, Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory, FileField
from factory.fuzzy import FuzzyChoice
from faker import Faker

UserModel = get_user_model()
fake_ja = Faker('ja_JP')
fake_en = Faker('en_US')
# Faker.seed(0)

tz_jst = datetime.timezone(datetime.timedelta(hours=9))

PUBLIC_SET = [x[0] for x in Tip.PUBLIC_SET_CHOICES]
CATEGORY = [x[0] for x in Notification.CATEGORY_CHOICES]


class TipFactory(DjangoModelFactory):


    class Meta:
        model = Tip

    title = fake_ja.word()
    description = fake_ja.paragraph(nb_sentences=3)
    tweet = fake_ja.word()
    created_by = SubFactory(UserFactory)
    created_at = fake_ja.date_time_this_year(tzinfo=tz_jst)
    updated_at = fake_ja.date_time_this_year(tzinfo=tz_jst)
    public_set = FuzzyChoice(PUBLIC_SET)


    @post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class CodeFactory(DjangoModelFactory):
    class Meta:
        model = Code

    tip = SubFactory(TipFactory)
    filename = fake_ja.file_name(category='text')
    content = fake_en.sentence(nb_words=5)


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    tip = SubFactory(TipFactory)
    no = Sequence(lambda n: n)
    text = fake_ja.text(max_nb_chars=20)
    created_by = SubFactory(UserFactory)
    created_at = fake_ja.date_time_this_year(tzinfo=tz_jst)

    @post_generation
    def to_users(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for user in extracted:
                self.to_users.add(user)


class LikeFactory(DjangoModelFactory):
    class Meta:
        model = Like

    tip = SubFactory(TipFactory)
    created_by = SubFactory(UserFactory)
    created_at = fake_ja.date_time_this_year(tzinfo=tz_jst)


class NotificationFactory(DjangoModelFactory):
    
    class Meta:
        model = Notification

    to_user = SubFactory(UserFactory)
    category = FuzzyChoice(CATEGORY)
    tip = SubFactory(TipFactory)
    content = fake_ja.text(max_nb_chars=20)
    created_at = fake_ja.date_time_this_year(tzinfo=tz_jst)
    created_by = SubFactory(UserFactory)
