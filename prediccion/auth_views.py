from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

from .models import Person, User
from .serializers import UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    POST /api/auth/login/
    Body: { "login": "...", "password": "..." }
    Returns: { "token": "...", "user": { ... } }
    """
    login_val = request.data.get('login', '').strip()
    password  = request.data.get('password', '')

    if not login_val or not password:
        return Response(
            {'detail': 'Login y contraseña son requeridos.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=login_val, password=password)

    if user is None:
        return Response(
            {'detail': 'Credenciales incorrectas.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'detail': 'Cuenta desactivada.'},
            status=status.HTTP_403_FORBIDDEN
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user':  UserSerializer(user).data,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """
    POST /api/auth/register/
    Body: { "login": "...", "password": "...", "first_name": "...", "last_name": "...", "email": "..." }
    Returns: { "token": "...", "user": { ... } }
    """
    login_val  = request.data.get('login', '').strip()
    password   = request.data.get('password', '')
    first_name = request.data.get('first_name', '').strip()
    last_name  = request.data.get('last_name', '').strip()
    email      = request.data.get('email', '').strip()

    # Validations
    if not login_val or not password or not first_name or not last_name:
        return Response(
            {'detail': 'Nombre, apellido, usuario y contraseña son obligatorios.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(login_val) < 4:
        return Response(
            {'login': ['El usuario debe tener al menos 4 caracteres.']},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(password) < 8:
        return Response(
            {'password': ['La contraseña debe tener al menos 8 caracteres.']},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(login=login_val).exists():
        return Response(
            {'login': ['Ese nombre de usuario ya está en uso.']},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create person + user
    person = Person.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=email,
    )
    user = User.objects.create_user(
        login=login_val,
        password=password,
        person=person,
    )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user':  UserSerializer(user).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """
    POST /api/auth/logout/
    Header: Authorization: Token <token>
    Deletes the token — user must login again.
    """
    try:
        request.user.auth_token.delete()
    except Exception:
        pass

    return Response(
        {'detail': 'Sesión cerrada correctamente.'},
        status=status.HTTP_200_OK
    )