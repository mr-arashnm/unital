```markdown
# سند معماری فنی - سیستم مدیریت مجتمع‌ها

## ۱. انتخاب تکنولوژی‌ها

### Backend: Django + Django REST Framework
**دلایل انتخاب:**
- ORM قوی برای مدل‌های پیچیده
- امنیت بالا و احراز هویت built-in
- جامعه بزرگ و منابع آموزشی
- مناسب برای MVP سریع

### Frontend: React + TypeScript
**دلایل انتخاب:**
- reusable components برای رابط‌های مشابه
- ecosystem قوی برای state management
- مناسب برای توسعه تیم‌های بزرگ
- قابلیت توسعه به موبایل (React Native)

### Database: PostgreSQL
**دلایل انتخاب:**
- پشتیبانی از JSON fields برای داده‌های پویا
- performance بالا برای تراکنش‌های مالی
- قابلیت‌های پیشرفته گزارش‌گیری
- مطابقت با نیازهای پیچیده دیتابیس

## ۲. ساختار پروژه

### Backend Structure:
```

backend/
├── accounts/          # مدیریت کاربران و احراز هویت
├── complexes/         # مدل‌های مجتمع و واحدها
├── financial/         # شارژ، تراکنش‌ها، حسابداری
├── operations/        # مدیریت تیم‌ها و وظایف
├── communications/    # نوتیفیکیشن و اطلاع‌رسانی
├── core/              # تنظیمات و utilities
└── api/               # endpoints و serializers

```
### Frontend Structure:
```

frontend/
├── public/
├── src/
│   ├── components/    # کامپوننت‌های قابل استفاده مجدد
│   ├── pages/         # صفحات اصلی
│   ├── services/      # API calls
│   ├── store/         # state management (Redux)
│   ├── types/         # TypeScript definitions
│   └── utils/         # helper functions

```
## ۳. مدل‌های اصلی دیتابیس

### کاربران و دسترسی‌ها:
```python
class User(AbstractUser):
    USER_TYPES = (
        ('resident', 'ساکن'),
        ('owner', 'مالک'),
        ('manager', 'مدیر'),
        ('staff', 'کارمند'),
        ('board_member', 'عضو هیئت مدیره'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone = models.CharField(max_length=15)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    complexes = models.ManyToManyField('Complex', through='UserComplexRole')
```

### مدیریت مجتمع‌ها و واحدها:

```python
class Complex(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    type = models.CharField(max_length=20, choices=[
        ('residential', 'مسکونی'),
        ('commercial', 'تجاری'),
        ('office', 'اداری'),
        ('mixed', 'ترکیبی')
    ])
    total_units = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class Building(models.Model):
    complex = models.ForeignKey(Complex, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    floors = models.IntegerField()

class Unit(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    unit_number = models.CharField(max_length=20)
    floor = models.IntegerField()
    area = models.DecimalField(max_digits=10, decimal_places=2)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_units')
    current_resident = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='residing_units')
```

### سیستم مالی:

```python
class ChargeTemplate(models.Model):
    complex = models.ForeignKey(Complex, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    cycle = models.CharField(max_length=20, choices=[
        ('monthly', 'ماهیانه'),
        ('quarterly', 'سه ماهه'),
        ('yearly', 'سالانه')
    ])

class Charge(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    template = models.ForeignKey(ChargeTemplate, on_delete=models.CASCADE)
    period = models.CharField(max_length=7)  # YYYY-MM
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'در انتظار'),
        ('paid', 'پرداخت شده'),
        ('overdue', 'معوقه')
    ])

class Transaction(models.Model):
    charge = models.ForeignKey(Charge, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    payment_date = models.DateTimeField(auto_now_add=True)
    reference_id = models.CharField(max_length=100)
    payment_gateway = models.CharField(max_length=50)
```

### مدیریت تیم‌ها و وظایف:

```python
class Team(models.Model):
    complex = models.ForeignKey(Complex, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    team_type = models.CharField(max_length=20, choices=[
        ('security', 'حفاظت'),
        ('maintenance', 'تاسیسات'),
        ('cleaning', 'نظافت'),
        ('landscaping', 'فضای سبز')
    ])

class Task(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'در انتظار'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'انجام شده'),
        ('cancelled', 'لغو شده')
    ])
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
```

## ۴. APIهای اصلی

### احراز هویت:

```python
class LoginAPI(APIView):
    def post(self, request):
        # لاگین با موبایل/ایمیل + رمزعبور
        pass

class UserProfileAPI(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
```

### مدیریت مجتمع:

```python
class ComplexViewSet(ModelViewSet):
    queryset = Complex.objects.all()
    serializer_class = ComplexSerializer
    permission_classes = [IsAuthenticated, IsManagerOrBoardMember]

class UnitViewSet(ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]
```

### سیستم مالی:

```python
class ChargeViewSet(ModelViewSet):
    queryset = Charge.objects.all()
    serializer_class = ChargeSerializer

class TransactionViewSet(ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
```

### مدیریت عملیات:

```python
class TeamViewSet(ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
```

## ۵. تنظیمات توسعه

### requirements.txt (Backend):

```
Django==4.2.0
djangorestframework==3.14.0
django-cors-headers==4.0.0
psycopg2-binary==2.9.6
Pillow==9.5.0
celery==5.3.0
redis==4.5.0
```

### package.json (Frontend):

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "redux": "^4.2.1",
    "axios": "^1.4.0",
    "react-router-dom": "^6.8.0"
  }
}
```

## ۶. دپلوی و DevOps

### docker-compose.yml:

```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: complex_manager
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password

  backend:
    build: ./backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

## ۷. محیط‌های توسعه

### محیط توسعه (Development):

- Django Debug Toolbar فعال
- CORS برای localhost:3000 فعال
- دیتابیس تست با داده‌های نمونه

### محیط استیجینگ (Staging):

- شبیه‌سازی production
- داده‌های واقعی اما تستی
- monitoring فعال

### محیط تولید (Production):

- debug غیرفعال
- static files در CDN
- database replication
- backup خودکار

## ۸. امنیت

### اقدامات امنیتی:

- احراز هویت JWT
- HTTPS اجباری
- محدودیت نرخ درخواست (Rate Limiting)
- محافظت در برابر CSRF و XSS
- رمزنگاری داده‌های حساس
- audit log برای تغییرات مهم
  ```
