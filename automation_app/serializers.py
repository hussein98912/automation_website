from rest_framework import serializers
from .models import Category, Service, Order,Project,ChatHistory
from .price import calculate_order_price

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

class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = "__all__"

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'id',
            'service',
            'industry',
            'host_duration',
            'workflow_name',
            'workflow_details',
            'total_price',
        ]
        read_only_fields = ['total_price']
