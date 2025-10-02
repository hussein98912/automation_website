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
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ChatHistory
from automation_app.Ai import ai_chat_response
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ChatHistory, Order, Service
from django.contrib.auth import get_user_model
from .Ai import ai_chat_response, suggest_workflow_name, suggest_workflow_details




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
    permission_classes = [AllowAny]


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]



import re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Service, Order, ChatHistory
from .utils import suggest_workflow_name, suggest_workflow_details  # افترض وجود دوال الاقتراح

User = get_user_model()

# حفظ الحالة المؤقتة لكل مستخدم
ORDER_TEMP = {}

# كلمات مفتاحية للخدمات
SERVICE_KEYWORDS = {
    "workflow automation": "Workflow Automation",
    "robotic process automation": "Robotic Process Automation",
    "rpa": "Robotic Process Automation",
    "ai chatbot": "AI Chatbot",
    "chatbot": "AI Chatbot",
    "predictive analytics": "Predictive Analytics",
    "workflow design": "Workflow Design"
}

# دالة لتطبيع النصوص (إزالة الأحرف الخاصة وتحويله لصغير)
def normalize_text(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

@api_view(["POST"])
def chatbot_api(request):
    user_id = request.data.get("user_id", None)
    message = request.data.get("message", "")
    files = request.FILES.get("attachment", None)

    user = User.objects.filter(id=user_id).first() if user_id else None

    # استرجاع آخر 5 محادثات
    history_qs = ChatHistory.objects.filter(user_id=user_id).order_by("-timestamp")[:5]
    history = [{"q": h.message, "a": h.response} for h in history_qs][::-1]

    bot_reply = ""
    
    # الحالة المؤقتة للطلب
    temp_order = ORDER_TEMP.get(user_id, {
        "service": None,
        "host_duration": None,
        "workflow_name": None,
        "workflow_details": None,
        "attachment": None
    })

    normalized_msg = normalize_text(message)

    # ===== خطوة 1: اختيار الخدمة =====
    if not temp_order["service"]:
        found_service = None
        # البحث بالكلمات المفتاحية
        for key, svc_name in SERVICE_KEYWORDS.items():
            if normalize_text(key) in normalized_msg:
                found_service = Service.objects.filter(title__icontains=svc_name).first()
                break
        # البحث بالاسم الكامل
        if not found_service:
            for svc in Service.objects.all():
                if normalize_text(svc.title) in normalized_msg:
                    found_service = svc
                    break

        if found_service:
            temp_order["service"] = found_service
            bot_reply = f"✅ Great! You selected **{found_service.title}**.\nWhich hosting plan do you want? (1 month, 3 months, 6 months, 12 months)"
        else:
            bot_reply = "Hello! Which service do you want to automate? (Workflow Automation, RPA, AI Chatbot, Predictive Analytics, Workflow Design)"

    # ===== خطوة 2: اختيار مدة الاستضافة =====
    elif not temp_order["host_duration"]:
        durations = ["1 month", "3 months", "6 months", "12 months"]
        selected = next((d for d in durations if normalize_text(d) in normalized_msg), None)
        if selected:
            temp_order["host_duration"] = selected
            bot_reply = "Perfect! What should be the workflow name? You can ask me to suggest one by typing 'suggest'."
        else:
            bot_reply = "Please select a valid hosting duration: 1 month, 3 months, 6 months, 12 months."

    # ===== خطوة 3: اسم الوركفلو =====
    elif not temp_order["workflow_name"]:
        if "suggest" in normalized_msg:
            temp_order["workflow_name"] = suggest_workflow_name(temp_order["service"].title)
            bot_reply = f"I suggest the workflow name: **{temp_order['workflow_name']}**.\nCan you provide the workflow details or ask me to suggest them?"
        else:
            temp_order["workflow_name"] = message
            bot_reply = "Got it! Can you provide the workflow details? You can ask me to suggest them."

    # ===== خطوة 4: تفاصيل الوركفلو =====
    elif not temp_order["workflow_details"]:
        if "suggest" in normalized_msg:
            temp_order["workflow_details"] = suggest_workflow_details(temp_order["workflow_name"])
            bot_reply = f"I suggest the workflow details:\n{temp_order['workflow_details']}\nDo you want to attach a file to your order? (Optional)"
        else:
            temp_order["workflow_details"] = message
            bot_reply = "Do you want to attach a file to your order? (Optional)"

    # ===== خطوة 5: المرفقات والتأكيد =====
    else:
        temp_order["attachment"] = files
        if user and temp_order["service"]:
            order = Order.objects.create(
                user=user,
                service=temp_order["service"],
                host_duration=temp_order["host_duration"],
                workflow_name=temp_order["workflow_name"],
                workflow_details=temp_order["workflow_details"],
                attachment=temp_order["attachment"]
            )
            bot_reply = f"✅ Your order has been created! Order ID: {order.id}"
            ORDER_TEMP.pop(user_id)  # مسح الحالة المؤقتة بعد الإنشاء

    # حفظ المحادثة
    ChatHistory.objects.create(user_id=user_id or "guest", message=message, response=bot_reply)

    # تحديث الحالة المؤقتة
    ORDER_TEMP[user_id] = temp_order

    return Response({
        "user_message": message,
        "bot_response": bot_reply,
        "conversation": history + [{"q": message, "a": bot_reply}]
    })

