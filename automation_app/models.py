from django.db import models
from django.contrib.auth.models import AbstractUser,User
from django.db import models
from django.conf import settings
from .price import calculate_order_price

class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(unique=True)

    REQUIRED_FIELDS = ["full_name", "email", "phone_number"]
    # username و password موجودة في AbstractUser


# ===========================
#  تصنيف الخدمات (Category)
# ===========================
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# ===========================
#  الخدمات (Service)
# ===========================
class Service(models.Model):
    icon = models.ImageField(upload_to="service_icons/", blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    features = models.JSONField(default=list, blank=True)
    #price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# ===========================
# ===========================
class Project(models.Model):
    id = models.SlugField(primary_key=True, unique=True)  # e.g. "student-management"
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    problem = models.TextField(blank=True, null=True)
    outcome = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100)
    image = models.ImageField(upload_to="project_images/", blank=True, null=True)

    technologies = models.JSONField(default=list, blank=True)
    features = models.JSONField(default=list, blank=True)

    price = models.CharField(max_length=50, blank=True, null=True)  # "$2,499"
    timeline = models.CharField(max_length=100, blank=True, null=True)  # "2-3 weeks"
    complexity = models.CharField(max_length=50, blank=True, null=True)  # "Advanced"

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# ===========================
#  الطلبات (Order)
# ===========================
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    HOST_DURATION_CHOICES = [
        ("1_month", "1 month"),
        ("3_months", "3 months"),
        ("6_months", "6 months"),
        ("12_months", "12 months"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="orders"
    )
    workflow_name = models.CharField(max_length=200, blank=True)
    workflow_details = models.TextField(blank=True)
    attachment = models.FileField(upload_to='orders_attachments/', blank=True, null=True)
    
    host_duration = models.CharField(
        max_length=20,
        choices=HOST_DURATION_CHOICES,
        default="1_month",
        help_text="مدة الاستضافة للخدمة"
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    industry = models.CharField(max_length=50, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate total price from KB
        self.total_price = calculate_order_price(self.service.title, self.host_duration)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


# ===========================
#  الدفع (Payment)
# ===========================
class Payment(models.Model):
    METHOD_CHOICES = [
        ("paypal", "PayPal"),
        ("stripe", "Stripe"),
        ("credit_card", "Credit Card"),
        ("bank_transfer", "Bank Transfer"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id}"





class ChatHistory(models.Model):
    user_id = models.CharField(max_length=100)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_bot = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user_id} - {self.timestamp}"

