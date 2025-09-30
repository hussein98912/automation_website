from rest_framework import serializers
from .models import Category, Service, Order,Project

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'service', 'host_duration', 'total_price']
        read_only_fields = ['total_price']

    def create(self, validated_data):
        user = self.context['request'].user
        service = validated_data['service']
        host_duration = validated_data['host_duration']

        # Calculate total_price based on host_duration
        multiplier = {
            '1_month': 1,
            '3_months': 3,
            '6_months': 6,
            '12_months': 12
        }
        total_price = service.price * multiplier.get(host_duration, 1)

        order = Order.objects.create(
            user=user,
            service=service,
            host_duration=host_duration,
            total_price=total_price
        )
        return order
    