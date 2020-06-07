import requests
import logging
from django.db import models


class Transaction(models.Model):
    """
    A model representing Transactions.
    """

    class TransactionStatuses(models.TextChoices):
        rejected = 'R', 'rejected'
        outgoing = 'O', 'outgoing'

    amount = models.IntegerField()
    destination = models.CharField(max_length=100)
    status = models.CharField(max_length=2, choices=TransactionStatuses.choices)

    def __str__(self):
        return f'Transaction {self.pk}: {self.amount} to {self.destination} marked {self.get_status_display()}'

    def __repr__(self):
        return str(self)

    @staticmethod
    def transaction_status_test(transaction: dict) -> TransactionStatuses:
        """
        Returns the status of a transaction, according to a set of rules.

        :param transaction: a dictionary representing a "soon to be" transaction.
        """

        for rule in Rule.objects.all():
            try:
                if rule.amount_is_valid(transaction['amount']) and \
                        rule.destination_is_valid(transaction['destination']):
                    return Transaction.TransactionStatuses.outgoing

            except Rule.CurrencyConvertingError as e:
                logging.warning(f'Could not finish transaction status test on rule {rule} because of api error.\n'
                                f'Error: {e}')
            except Exception:
                logging.exception(f'Ran into an unknown exception when running {rule}.\n')

        return Transaction.TransactionStatuses.rejected


class Rule(models.Model):
    """
    A model representing a PolicyRule
    """

    class CurrencyConvertingError(Exception):
        """
        Raised when the currency conversion is unsuccessful.
        The error is returned.
        """
        pass

    rule_id = models.AutoField(primary_key=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    amount = models.IntegerField(default=-1)
    currency = models.CharField(max_length=10, default='satoshi')

    class Meta:
        ordering = ['created_datetime']

    def __str__(self):
        return f'Rule: {self.rule_id}, Created: {self.created_datetime},' \
               f' Amount: {self.amount} {self.currency}, Destinations: {self.destinations.all()}'

    def __repr__(self):
        return str(self)

    def amount_is_valid(self, amount: int) -> bool:
        """
        Returns whether a given amount of satoshis passes this rule.
        True is returned if:
            * The amount given is lower than the rule's threshold
            * The threshold is -1

        :param amount: the amount of satoshis to test
        """
        return self.amount == -1 or amount <= self.get_amount_in_satoshis()

    def destination_is_valid(self, destination: str) -> bool:
        """
        Returns whether a destination passes this rule.
        True is returned if:
            * The given destination is in this rule's list of destinations
            * The destination list is empty

        :param destination: the destination to test
        """
        return self.destinations.count() == 0 or \
               self.destinations.filter(destination_name=destination).count() != 0

    def get_amount_in_satoshis(self) -> int:
        """
        Returns the rule's amount property in satoshis.
        """
        if self.currency != 'satoshi':
            return self._get_exchange_rate_to_satoshis() * self.amount
        return self.amount

    def _get_exchange_rate_to_satoshis(self) -> int:
        """
        Returns the exchange rate for the currency of the given rule to satoshis
        by querying an api.

        :raises CurrencyConvertingError if the rest api doesn't respond as expected.
        """
        CURRENCY_CONVERTING_REST_API = 'https://blockchain.info/tobtc?currency={currency}&value={amount}'
        BITCOIN_TO_SATOSHIS = 10 ** 8

        url = CURRENCY_CONVERTING_REST_API.format(currency=self.currency, amount=self.amount)
        try:
            response = requests.get(url)
            exchange_rate = int(float(response.content) * BITCOIN_TO_SATOSHIS)
        except Exception:
            raise Rule.CurrencyConvertingError(f'Status Code: {response.status_code}, Message: {response.text}')

        logging.debug(f'Successful request to {url}.'
                      f'Response is {response.status_code}, {response.text}')
        return exchange_rate


class Destination(models.Model):
    """
    A model representing a possible destination in a policy Rule object
    """
    destination_name = models.CharField(max_length=100)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='destinations')

    def __repr__(self):
        return self.destination_name
