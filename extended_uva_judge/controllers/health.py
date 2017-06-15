from flask import Blueprint, Response

mod = Blueprint('health', __name__, url_prefix='')


@mod.route('/health')
def health():
    return Response('OK', status=200)
