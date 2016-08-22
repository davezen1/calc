import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.contrib.auth.models import User


def path(*paths):
    root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(root_dir, *paths)


FAKE_SCHEDULE = 'data_capture.schedules.fake_schedule.FakeSchedulePriceList'

FAKE_SCHEDULE_EXAMPLE_PATH = path(
    'static', 'data_capture', 'fake_schedule_example.csv'
)

R10_XLSX_PATH = path('static', 'data_capture', 'r10_export_sample.xlsx')

XLSX_CONTENT_TYPE = ('application/vnd.openxmlformats-'
                     'officedocument.spreadsheetml.sheet')


def uploaded_csv_file(content=None):
    if content is None:
        with open(FAKE_SCHEDULE_EXAMPLE_PATH, 'rb') as f:
            content = f.read()

    return SimpleUploadedFile(
        'foo.csv',
        content,
        content_type='text/csv'
    )


def r10_file(content=None, name='r10.xlsx'):
    if content is None:
        with open(R10_XLSX_PATH, 'rb') as f:
            content = f.read()

    if type(content) is str:
        content = bytes(content, 'UTF-8')

    return SimpleUploadedFile(name, content,
                              content_type=XLSX_CONTENT_TYPE)


@override_settings(
    # This will make tests run faster.
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    # Ignore our custom auth backend so we can log the user in via
    # Django 1.8's login helpers.
    AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend'],
    DATA_CAPTURE_SCHEDULES=[FAKE_SCHEDULE],
)
class StepTestCase(TestCase):
    def login(self, is_staff=False):
        user = User.objects.create_user(
            username='foo',
            password='bar'
        )
        if is_staff:
            user.is_staff = True
            user.save()
        assert self.client.login(username='foo', password='bar')
        return user

    def assertRedirectsToLogin(self, url):
        res = self.client.get(url)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(
            res['Location'],
            'http://testserver/auth/login?next=%s' % url
        )

    def assertHasMessage(self, res, tag, content):
        msgs = list(res.context['messages'])
        self.assertEqual(len(msgs), 1)
        m = msgs[0]
        self.assertEqual(m.tags, tag)
        self.assertEqual(str(m), content)
