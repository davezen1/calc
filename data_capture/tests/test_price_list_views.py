import json

from ..models import SubmittedPriceList
from ..schedules.fake_schedule import FakeSchedulePriceList
from ..schedules import registry
from .common import StepTestCase, FAKE_SCHEDULE, FAKE_SCHEDULE_EXAMPLE_PATH


class PriceListStepTestCase(StepTestCase):
    def set_fake_gleaned_data(self, rows):
        session = self.client.session
        pricelist = FakeSchedulePriceList(rows)
        session['data_capture:schedule'] = registry.get_classname(pricelist)
        session['data_capture:gleaned_data'] = registry.serialize(pricelist)
        session.save()

    def setUp(self):
        registry._init()


class Step1Tests(PriceListStepTestCase):
    url = '/data-capture/step/1'

    csvpath = FAKE_SCHEDULE_EXAMPLE_PATH

    def ajax_post(self, data):
        res = self.client.post(self.url, data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        return res, json.loads(res.content.decode('utf-8'))

    def test_login_is_required(self):
        self.assertRedirectsToLogin(self.url)

    def test_get_is_ok(self):
        self.login()
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)

    def test_valid_post_sets_session_data(self):
        self.login()
        with open(self.csvpath) as f:
            self.client.post(self.url, {
                'schedule': FAKE_SCHEDULE,
                'file': f
            })
            self.assertEqual(self.client.session['data_capture:schedule'],
                             FAKE_SCHEDULE)
            gleaned_data = self.client.session['data_capture:gleaned_data']
            gleaned_data = registry.deserialize(gleaned_data)
            assert isinstance(gleaned_data, FakeSchedulePriceList)
            self.assertEqual(gleaned_data.rows, [{
                'education': 'Bachelors',
                'price': '15.00',
                'service': 'Project Manager',
                'sin': '132-40',
                'years_experience': '7'
            }])

    def test_valid_post_redirects_to_step_2(self):
        self.login()
        with open(self.csvpath) as f:
            res = self.client.post(self.url, {
                'schedule': FAKE_SCHEDULE,
                'file': f
            })
            self.assertRedirects(res, Step2Tests.url)

    def test_valid_post_via_xhr_returns_json(self):
        self.login()
        with open(self.csvpath) as f:
            res, json_data = self.ajax_post({
                'schedule': FAKE_SCHEDULE,
                'file': f
            })
            self.assertEqual(json_data, {
                'redirect_url': '/data-capture/step/2'
            })

    def test_invalid_post_returns_html(self):
        self.login()
        res = self.client.post(self.url, {
            'schedule': FAKE_SCHEDULE
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, r'<!DOCTYPE html>')
        self.assertContains(res, r'This field is required')
        self.assertHasMessage(
            res,
            'error',
            'Oops, please correct the error below and try again.'
        )

    def test_invalid_post_via_xhr_returns_json(self):
        self.login()
        res, json_data = self.ajax_post({'schedule': FAKE_SCHEDULE})
        assert '<!DOCTYPE html>' not in json_data['form_html']
        self.assertRegexpMatches(json_data['form_html'],
                                 r'This field is required')
        self.assertHasMessage(
            res,
            'error',
            'Oops, please correct the error below and try again.'
        )


class Step2Tests(PriceListStepTestCase):
    url = '/data-capture/step/2'

    def test_login_is_required(self):
        self.assertRedirectsToLogin(self.url)

    def test_gleaned_data_is_required(self):
        self.login()
        res = self.client.get(self.url)
        self.assertRedirects(res, Step1Tests.url)


class Step3Tests(PriceListStepTestCase):
    url = '/data-capture/step/3'

    rows = [{
        'education': 'Bachelors',
        'price': '15.00',
        'service': 'Project Manager',
        'sin': '132-40',
        'years_experience': '7'
    }]

    valid_form = {
        'contract_number': 'GS-123-4567',
        'vendor_name': 'foo',
        'contractor_site': 'Customer',
        'is_small_business': False
    }

    def test_login_is_required(self):
        self.assertRedirectsToLogin(self.url)

    def test_gleaned_data_is_required(self):
        self.login()
        res = self.client.get(self.url)
        self.assertRedirects(res, Step1Tests.url)

    def test_gleaned_data_with_valid_rows_is_required(self):
        self.login()
        self.set_fake_gleaned_data([])
        res = self.client.get(self.url)
        self.assertRedirects(res, Step2Tests.url)

    def test_get_is_ok(self):
        self.login()
        self.set_fake_gleaned_data(self.rows)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)

    def test_valid_post_clears_gleaned_data(self):
        self.login()
        self.set_fake_gleaned_data(self.rows)
        self.client.post(self.url, self.valid_form)
        assert 'data_capture:gleaned_data' not in self.client.session

    def test_valid_post_creates_models(self):
        user = self.login()
        self.set_fake_gleaned_data(self.rows)
        self.client.post(self.url, self.valid_form)
        p = SubmittedPriceList.objects.filter(
            contract_number='GS-123-4567'
        )[0]
        self.assertEqual(p.vendor_name, 'foo')
        self.assertEqual(p.contractor_site, 'Customer')
        self.assertEqual(p.submitter, user)
        self.assertEqual(p.schedule, FAKE_SCHEDULE)

        gleaned_data = registry.deserialize(
            json.loads(p.serialized_gleaned_data)
        )
        assert isinstance(gleaned_data, FakeSchedulePriceList)
        self.assertEqual(gleaned_data.rows, self.rows)

        self.assertEqual(p.rows.count(), 1)
        row = p.rows.all()[0]
        self.assertEqual(row.current_price, 15)

    def test_valid_post_redirects_to_step_4(self):
        self.login()
        self.set_fake_gleaned_data(self.rows)
        res = self.client.post(self.url, self.valid_form)
        self.assertRedirects(res, Step4Tests.url)

    def test_invalid_post_returns_html(self):
        self.login()
        self.set_fake_gleaned_data(self.rows)
        res = self.client.post(self.url, {})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'This field is required')
        self.assertHasMessage(
            res,
            'error',
            'Oops, please correct the errors below and try again.'
        )


class Step4Tests(StepTestCase):
    url = '/data-capture/step/4'

    def test_get_is_ok(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
