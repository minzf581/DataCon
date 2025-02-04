from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed

class RootAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_authenticated:
            raise AuthenticationFailed()
        return Response({
            'message': 'Welcome to the API',
            'version': 'v1'
        })

class RestrictedAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_authenticated:
            raise AuthenticationFailed()
        return Response({
            'message': 'This is a restricted endpoint',
            'user': request.user.username
        })

    def post(self, request):
        raise AuthenticationFailed() 