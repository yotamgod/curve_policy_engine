from rest_framework import viewsets, mixins
from rest_api.models import Rule, Transaction
from rest_api.serializers import RuleSerializer, TransactionSerializer


class PolicyRuleViewSet(viewsets.ModelViewSet):
    """
    A ModelSetView of PolicyRules - supplies CRUD operations to Rule models.
    """
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer


class TransactionViewSet(viewsets.GenericViewSet,
                         mixins.CreateModelMixin,
                         mixins.ListModelMixin):
    """
    Supplies Create and List operations to Transaction models.

    """
    serializer_class = TransactionSerializer

    def get_queryset(self):
        """
        Returns a the queryset of transactions that matches the optional filter keyword.
        If there is no keyword, or the value of the keyword is 'all', returns the entire queryset.
        If the keyword is one of the TransactionStatuses, returns the transactions that match said status.
        Otherwise, returns an empty queryset.
        """
        transaction_filter = self.request.query_params.get('filter', None)
        if not transaction_filter or transaction_filter == 'all':
            queryset = Transaction.objects.all()
        else:
            try:
                queryset = Transaction.objects.filter(
                    status=Transaction.TransactionStatuses[transaction_filter])
            except KeyError:
                queryset = []

        return queryset
