from django.test import TestCase


class StyleguideTests(TestCase):

    def test_styleguide_returns_200(self):
        response = self.client.get('/styleguide/')
        self.assertEqual(response.status_code, 200)

    def test_styleguide_ajaxform_returns_200(self):
        response = self.client.get('/styleguide/ajaxform')
        self.assertEqual(response.status_code, 200)
