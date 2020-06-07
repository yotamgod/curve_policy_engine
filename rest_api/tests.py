from unittest import mock
from urllib.parse import parse_qs, urlparse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_api.models import Rule, Transaction, Destination


class RuleCrudTests(APITestCase):

    def setUp(self) -> None:
        rule = Rule.objects.create(amount=100, currency='USD')
        Destination.objects.create(rule=rule, destination_name='home')

    def test_create_currency_rule(self):
        response = self.client.post('/rest_api/policy_rule/',
                                    data={'amount': 10, 'destinations': ['c'], 'currency': 'USD'},
                                    format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rule.objects.all().count(), 2)
        self.assertEqual(Destination.objects.all().count(), 2)

    def test_create_no_currency_rule(self):
        response = self.client.post('/rest_api/policy_rule/',
                                    data={'amount': 1000, 'destinations': ['a', 'b']},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Rule.objects.all().count(), 2)
        self.assertEqual(Destination.objects.all().count(), 3)

    def test_delete_rule(self):
        self.client.delete('/rest_api/policy_rule/1/')
        self.assertEqual(Rule.objects.all().count(), 0)

    def test_update_rule(self):
        self.client.patch('/rest_api/policy_rule/1/', data={'amount': 200, 'currency': 'CAD'},
                          format='json')
        rule = Rule.objects.get(pk=1)
        self.assertEqual(rule.amount, 200)
        self.assertEqual(rule.currency, 'CAD')


class TransactionTests(APITestCase):

    @staticmethod
    def mock_get_exchange_rate(url):
        """
        Mocks requests.get in rest_api.models.
        Allowed currencies are USD and CAD, and exchange rate is always 100.

        """
        ALLOWED_CURRENCIES = ['USD', 'CAD']
        DEFAULT_EXCHANGE_RATE = 100
        mock_response = mock.Mock()
        parsed_url = urlparse(url)
        parsed_params = parse_qs(parsed_url.query)
        currency, value = parsed_params['currency'][0], parsed_params['value'][0]

        if currency in ALLOWED_CURRENCIES:
            mock_response.status_code = 200
            mock_response.content = str(DEFAULT_EXCHANGE_RATE * value)

        else:
            mock_response.status_code = 500
            mock_response.content = mock_response.text = str('Invalid Currency')
        return mock_response

    def setUp(self) -> None:
        self.mock_get_patcher = mock.patch('rest_api.models.requests.get')
        self.mock_get = self.mock_get_patcher.start()
        self.mock_get.side_effect = lambda url: self.mock_get_exchange_rate(url)

    def tearDown(self) -> None:
        self.mock_get_patcher.stop()

    def test_transaction_on_currency_rule(self):
        currency_rule = Rule.objects.create(amount=200, currency='USD')
        Destination.objects.create(rule=currency_rule, destination_name='home')

        self.client.post('/rest_api/transactions/',
                         data={'amount': 1, 'destination': 'home'},
                         format='json')

        self.assertEqual(Transaction.objects.get(pk=1).status,
                         Transaction.TransactionStatuses.outgoing.value)

    def test_transaction_on_satoshi_rule(self):
        no_currency_rule = Rule.objects.create(amount=10000)
        Destination.objects.create(rule=no_currency_rule, destination_name='work')

        self.client.post('/rest_api/transactions/',
                         data={'amount': 20000, 'destination': 'work'},
                         format='json')

        self.assertEqual(Transaction.objects.get(pk=1).status,
                         Transaction.TransactionStatuses.rejected.value)

    def test_bad_currency_rule_transaction(self):
        bad_currency_rule = Rule.objects.create(amount=100, currency='bad_crncy')
        Destination.objects.create(rule=bad_currency_rule, destination_name='home')

        self.client.post('/rest_api/transactions/',
                         data={'amount': 50, 'destination': 'home'},
                         format='json')

        self.assertEqual(Transaction.objects.get(pk=1).status,
                         Transaction.TransactionStatuses.rejected.value)

    def test_any_amount_rule_transaction(self):
        any_amount_rule = Rule.objects.create(amount=-1)
        Destination.objects.create(rule=any_amount_rule, destination_name='my_pocket')

        self.client.post('/rest_api/transactions/',
                         data={'amount': 6000, 'destination': 'my_pocket'},
                         format='json')

        self.assertEqual(Transaction.objects.get(pk=1).status,
                         Transaction.TransactionStatuses.outgoing.value)

    def test_any_destination_rule_transaction(self):
        any_destination_rule = Rule.objects.create(amount=10)
        self.client.post('/rest_api/transactions/',
                         data={'amount': 10, 'destination': 'shady_place'},
                         format='json')
        self.client.post('/rest_api/transactions/',
                         data={'amount': 100, 'destination': 'shady_place'},
                         format='json')
        self.assertEqual(Transaction.objects.get(pk=1).status,
                         Transaction.TransactionStatuses.outgoing.value)
        self.assertEqual(Transaction.objects.get(pk=2).status,
                         Transaction.TransactionStatuses.rejected.value)
