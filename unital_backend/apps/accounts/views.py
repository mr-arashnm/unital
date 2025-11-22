from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserRegistrationSerializer, UserProfileSerializer
from drf_spectacular.utils import extend_schema
from .serializers import UserLoginSerializer

@extend_schema(request=UserRegistrationSerializer, responses={201: UserRegistrationSerializer})
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    signup new user
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # create JWT token for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Registration successful',
            'user_id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh)
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(request=UserLoginSerializer, responses={200: UserProfileSerializer})
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'email and password are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # احراز هویت کاربر
    user = authenticate(email=email, password=password)
    
    if not user:
        return Response(
            {'error': 'ایمیل یا رمز عبور اشتباه است'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not user.is_active:
        return Response(
            {'error': 'حساب کاربری غیرفعال است'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # ایجاد توکن JWT
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'message': 'ورود موفقیت‌آمیز بود',
        'user_id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'user_type': user.user_type,
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'access_token_expires_in': 3600,  # 1 hour
        'refresh_token_expires_in': 86400  # 24 hours
    }, status=status.HTTP_200_OK)

@extend_schema(responses={200: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    خروج کاربر - در JWT معمولاً سمت کلاینت توکن رو پاک می‌کنیم
    """
    # در JWT، logout معمولاً سمت کلاینت handle می‌شه
    # اما می‌تونیم توکن رو blacklist کنیم اگر نیاز باشه
    return Response({
        'message': 'خروج موفقیت‌آمیز بود'
    }, status=status.HTTP_200_OK)

@extend_schema(request=None, responses={200: None})
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    دریافت access token جدید با refresh token
    """
    refresh_token = request.data.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token الزامی است'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        user_id = refresh['user_id']
        user = User.objects.get(id=user_id)
        
        # ایجاد توکن جدید
        new_refresh = RefreshToken.for_user(user)
        
        return Response({
            'access_token': str(new_refresh.access_token),
            'refresh_token': str(new_refresh),
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Refresh token نامعتبر است'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@extend_schema(request=UserProfileSerializer, responses={200: UserProfileSerializer})
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    مشاهده و ویرایش پروفایل کاربر
    """
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'پروفایل با موفقیت به‌روزرسانی شد',
                'data': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(request=None, responses={200: None})
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_account_view(request):
    """
    تأیید حساب کاربری با کد
    """
    email = request.data.get('email')
    verification_code = request.data.get('verification_code')
    
    if not email or not verification_code:
        return Response(
            {'error': 'ایمیل و کد تأیید الزامی است'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        
        # اینجا منطق تأیید کد رو پیاده‌سازی کن
        # برای تست، هر کدی رو قبول می‌کنیم
        user.is_verified = True
        user.save()
        
        return Response({
            'message': 'حساب کاربری با موفقیت تأیید شد'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'کاربر یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@extend_schema(request=None, responses={200: None})
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_request_view(request):
    """
    درخواست بازنشانی رمز عبور
    """
    email = request.data.get('email')
    
    if not email:
        return Response(
            {'error': 'ایمیل الزامی است'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        
        # اینجا کد بازنشانی ایجاد و ارسال کن (ایمیل/SMS)
        # برای تست فقط پیام موفقیت برمی‌گردانیم
        
        return Response({
            'message': 'ایمیل بازنشانی رمز عبور ارسال شد'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        # برای امنیت، حتی اگر کاربر وجود نداشت هم پیام موفقیت بده
        return Response({
            'message': 'ایمیل بازنشانی رمز عبور ارسال شد'
        }, status=status.HTTP_200_OK)

@extend_schema(request=None, responses={200: None})
@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_confirm_view(request):
    """
    تأیید بازنشانی رمز عبور
    """
    email = request.data.get('email')
    verification_code = request.data.get('verification_code')
    new_password = request.data.get('new_password')
    
    if not all([email, verification_code, new_password]):
        return Response(
            {'error': 'تمام فیلدها الزامی هستند'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        
        # اینجا منطق تأیید کد رو پیاده‌سازی کن
        # برای تست، هر کدی رو قبول می‌کنیم
        
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'رمز عبور با موفقیت تغییر یافت'
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'کاربر یافت نشد'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@extend_schema(responses={200: None})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_complexes_view(request):
    """
    دریافت لیست مجتمع‌های مرتبط با کاربر
    """
    user = request.user
    complexes = []
    
    if user.user_type in ['manager', 'board_member']:
        from apps.complexes.models import Building
        complexes = Building.objects.filter(board_members=user)
    elif user.user_type == 'owner':
        from apps.complexes.models import Unit
        user_units = Unit.objects.filter(owner=user)
        complexes = list(set([unit.building.complex for unit in user_units]))
    elif user.user_type == 'resident':
        from apps.complexes.models import Unit
        user_units = Unit.objects.filter(current_resident=user)
        complexes = list(set([unit.building.complex for unit in user_units]))
    
    from apps.complexes.serializers import ComplexSerializer
    serializer = ComplexSerializer(complexes, many=True)
    
    return Response({
        'complexes': serializer.data
    }, status=status.HTTP_200_OK)