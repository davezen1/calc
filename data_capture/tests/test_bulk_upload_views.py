
from .common import StepTestCase


# TODO: Finish these tests
class Region10UploadStep1Tests(StepTestCase):
    url = '/data-capture/bulk/region-10/step/1'

    def test_login_is_required(self):
        self.assertRedirectsToLogin(self.url)

    def test_staff_login_is_required(self):
        self.login(is_staff=True)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)

    def test_non_staff_login_errors(self):
        self.login()
        res = self.client.get(self.url)
        # TODO: currently this redirects to
        # /admin/login/?next=/data-capture/bulk/region-10/step/1
        # but I think it should show a 403 page
        self.assertNotEqual(res.status_code, 200)


class Region10UploadStep2Tests(StepTestCase):
    url = '/data-capture/bulk/region-10/step/2'

    def test_login_is_required(self):
        self.assertRedirectsToLogin(self.url)


class Region10UploadStep3Tests(StepTestCase):
    url = '/data-capture/bulk/region-10/step/3'

    def test_login_is_required(self):
        self.assertRedirectsToLogin(self.url)
