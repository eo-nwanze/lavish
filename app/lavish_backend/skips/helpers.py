"""
Helper functions for skip views
"""

from django.http import JsonResponse


def json_response(data, status=200):
    """Helper to return consistent JSON responses"""
    return JsonResponse(data, status=status)


def error_response(message, status=400, errors=None):
    """Helper to return error responses"""
    response = {'success': False, 'error': message}
    if errors:
        response['errors'] = errors
    return JsonResponse(response, status=status)