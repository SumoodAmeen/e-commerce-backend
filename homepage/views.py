"""
DRF Views for HomepageHero.

Public GET endpoint for frontend.
Protected PUT endpoint for admin updates.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.cache import cache

from .models import HomepageHero
from .serializers import HomepageHeroSerializer, HomepageHeroUpdateSerializer
from catalog.permissions import IsAdminUser


class HomepageHeroView(APIView):
    """
    Singleton Hero endpoint.
    
    GET: Public - returns hero data (cached)
    PUT: Admin only - updates hero data
    """
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]
    
    def get(self, request):
        """
        Public GET endpoint.
        Returns hero data if active, otherwise 404-like response.
        """
        # Try cache first
        cached_data = cache.get('homepage_hero')
        if cached_data is not None:
            if not cached_data.get('is_active'):
                return Response(
                    {'detail': 'Hero section is currently disabled.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(cached_data)
        
        # Load from database
        try:
            hero = HomepageHero.objects.get(pk=1)
        except HomepageHero.DoesNotExist:
            return Response(
                {'detail': 'Hero section not configured.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not hero.is_active:
            return Response(
                {'detail': 'Hero section is currently disabled.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = HomepageHeroSerializer(hero, context={'request': request})
        data = serializer.data
        
        # Cache for 5 minutes
        cache.set('homepage_hero', data, 300)
        
        return Response(data)
    
    def put(self, request):
        """
        Admin PUT endpoint.
        Updates hero data.
        """
        try:
            hero = HomepageHero.objects.get(pk=1)
        except HomepageHero.DoesNotExist:
            hero = HomepageHero.load()
        
        serializer = HomepageHeroUpdateSerializer(
            hero,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
