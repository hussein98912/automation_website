from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth import authenticate
from django.contrib.auth import logout
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from .models import Order , Service
from rest_framework import generics, permissions
from .models import Category, Service, Order,Project
from .serializers import CategorySerializer, ServiceSerializer, OrderSerializer,ProjectSerializer


User = get_user_model()

@api_view(['POST'])
def signup_api(request):
    data = request.data
    required_fields = ["full_name", "address", "email", "phone_number", "username", "password"]
    
    # تحقق من وجود كل الحقول
    for field in required_fields:
        if field not in data:
            return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # تحقق من وجود username أو email مسبقًا
    if User.objects.filter(username=data["username"]).exists():
        return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=data["email"]).exists():
        return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    # إنشاء المستخدم
    user = User.objects.create_user(
        username=data["username"],
        password=data["password"],
        email=data["email"],
        full_name=data["full_name"],
        phone_number=data["phone_number"],
        address=data["address"]
    )
    
    login(request, user)  # تسجيل الدخول مباشرة بعد التسجيل
    return Response({"message": "Account created and logged in successfully!"}, status=status.HTTP_201_CREATED)



@csrf_exempt  # تجاهل CSRF
@api_view(['POST'])
@permission_classes([AllowAny])  # السماح لأي شخص بتسجيل الدخول
@authentication_classes([])  # تجاهل أي Authentication Class افتراضي
def login_api(request):
    data = request.data
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, username=username, password=password)
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": f"Welcome, {username}!",
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def logout_api(request):
    
    return Response({"message": "Logged out successfully. Delete the token in frontend."}, status=status.HTTP_200_OK)




@api_view(['POST'])
def create_order(request):
    data = request.data
    service_id = data.get("service_id")
    
    try:
        service = Service.objects.get(id=service_id)
    except Service.DoesNotExist:
        return Response({"error": "Service not found"}, status=404)
    
    order = Order(
        user=request.user,
        service=service,
        host_duration=data.get("host_duration", "1_month"),
        workflow_name=data.get("workflow_name", ""),
        workflow_details=data.get("workflow_details", "")
    )
    
    # Handle optional file attachment
    if 'attachment' in request.FILES:
        order.attachment = request.FILES['attachment']
    
    order.save() 
    
    return Response({
        "message": "Order created successfully!",
        "order_id": order.id,
        "total_price": order.total_price
    })


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]



class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer