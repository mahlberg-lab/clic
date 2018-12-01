'''
clic.uwsgi: UWSGI entry point
*****************************
'''
from clic.app import create_app

app = create_app()
