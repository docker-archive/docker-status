
import os


def deployment():
    '''Return production if we are in GoogleAppEngine else development'''
    return 'development' if os.environ.get('SERVER_SOFTWARE', '').startswith(
        'Development') else 'production'
