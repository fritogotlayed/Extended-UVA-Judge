"""Module to house the health check endpoint"""
from flask import Blueprint, Response

MOD = Blueprint('health', __name__, url_prefix='')


@MOD.route('/health')
def health():
    """Health check endpoint"""
    return Response('OK', status=200)
