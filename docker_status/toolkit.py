
import os


def deployment():
    '''Return production if we are in GoogleAppEngine else development'''
    test = os.environ.get('SERVER_SOFTWARE', '')
    return ('development' if test.startswith('Development') or test == ''
        else 'production')
