import logging
from rest_framework import serializers
from rest_api.models import Rule, Destination, Transaction


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = '__all__'

    def to_representation(self, instance: Destination) -> str:
        """
        Returns the repr of the Destination instance (just the destination name)

        :param instance: the Destination instance
        """
        return repr(instance)

    def to_internal_value(self, data: str) -> dict:
        """
        Returns a dictionary representing a destination

        :param data: a string including the destination's name
        """
        return {'destination_name': data}


class RuleSerializer(serializers.ModelSerializer):
    destinations = DestinationSerializer(many=True, read_only=False)

    class Meta:
        model = Rule
        fields = ('rule_id', 'amount', 'destinations', 'currency')

    def create(self, validated_data: dict) -> Rule:
        """
        Create and return a new 'Rule' instance, and create the relating 'Destination' instances.

        :param validated_data: the rule data received by the rest api
        """
        destinations = validated_data.pop('destinations')
        rule = Rule.objects.create(**validated_data)
        for destination in destinations:
            Destination.objects.create(rule=rule, destination_name=destination['destination_name'])

        logging.info(f'Created new rule: {rule}')
        return rule

    def update(self, instance: Rule, validated_data: dict) -> Rule:
        """
        Update and return an existing 'Rule' instance and its' Destination instances.

        :param instance: the Rule instance to be updated
        :param validated_data: a dictionary including the data with which to update the rule.
        """
        instance.amount = validated_data.get('amount', instance.amount)
        instance.currency = validated_data.get('currency', instance.currency)
        if 'destinations' in validated_data:
            instance.destinations.all().delete()
            for destination in validated_data['destinations']:
                Destination.objects.create(rule=instance, destination_name=destination['destination_name'])
        instance.save()
        logging.info(f'Updated rule value: {instance}')
        return instance


class TransactionSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Transaction
        fields = ('amount', 'destination', 'status')

    def create(self, validated_data: dict) -> Transaction:
        """
        Create and return a Transaction instance.

        :param validated_data: a dictionary used to create the Transaction
        """
        validated_data['status'] = Transaction.transaction_status_test(validated_data)
        transaction = Transaction.objects.create(**validated_data)
        logging.debug(f'New transaction created: {transaction}')
        return transaction
