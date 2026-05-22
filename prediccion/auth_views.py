from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserSerializer


def _get_tokens_for_user(user: User) -> dict:
    """
    Genera par de tokens JWT para un usuario.
    Retorna: { refresh: str, access: str }
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """
    POST /api/auth/login/
    Body: { login, password }
    Response: { access, refresh, user }
    """
    login_val = request.data.get('login', '').strip()
    password  = request.data.get('password', '').strip()

    if not login_val or not password:
        return Response(
            {'error': 'login y password son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    
    user = authenticate(request, username=login_val, password=password)

    if user is None:
        return Response(
            {'error': 'Credenciales incorrectas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {'error': 'Cuenta desactivada'},
            status=status.HTTP_403_FORBIDDEN
        )

    tokens = _get_tokens_for_user(user)
    user_data = UserSerializer(user).data

    return Response({
        'access':  tokens['access'],
        'refresh': tokens['refresh'],
        'user':    user_data,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """
    POST /api/auth/register/
    Body: { login, password, first_name, last_name, email }
    Response: { access, refresh, user }
    """
    from django.db import transaction
    from .models import Person, Role

    data       = request.data
    login_val  = data.get('login', '').strip()
    password   = data.get('password', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name  = data.get('last_name', '').strip()
    email      = data.get('email', '').strip()

    
    if not all([login_val, password, first_name, last_name]):
        return Response(
            {'error': 'login, password, first_name y last_name son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(login=login_val).exists():
        return Response(
            {'error': 'Ese login ya está en uso'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
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
            
            try:
                patient_role = Role.objects.get(description='patient')
                user.roles.add(patient_role)
            except Role.DoesNotExist:
                pass  # No bloquea el registro si el rol no existe

    except Exception as e:
        return Response(
            {'error': f'Error al crear usuario: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    tokens    = _get_tokens_for_user(user)
    user_data = UserSerializer(user).data

    return Response({
        'access':  tokens['access'],
        'refresh': tokens['refresh'],
        'user':    user_data,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """
    POST /api/auth/logout/
    Body: { refresh }  ← el frontend envía el refresh token para invalidarlo
    Blacklistea el refresh token para que no pueda usarse más.
    """
    refresh_token = request.data.get('refresh')

    if not refresh_token:
        
        return Response({'message': 'Sesión cerrada'}, status=status.HTTP_200_OK)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        
        pass

    return Response({'message': 'Sesión cerrada correctamente'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_reset_password(request):
    """
    POST /api/auth/reset-password/
    Body: { login, new_password }
    Busca el usuario por login, verifica que existe y actualiza la contraseña.
    """
    login_val    = request.data.get('login', '').strip()
    new_password = request.data.get('new_password', '').strip()

    if not login_val or not new_password:
        return Response(
            {'error': 'login y new_password son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if len(new_password) < 8:
        return Response(
            {'error': 'La contraseña debe tener mínimo 8 caracteres'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(login=login_val)
    except User.DoesNotExist:
        return Response(
            {'error': 'No existe un usuario con ese nombre'},
            status=status.HTTP_404_NOT_FOUND
        )

    user.set_password(new_password)
    user.save()

    return Response(
        {'message': 'Contraseña actualizada correctamente'},
        status=status.HTTP_200_OK
    )