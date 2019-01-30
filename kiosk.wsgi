import sys
import os
sys.path.insert(0, '/var/www/kiosk/')

f = open(os.devnull, 'w')
sys.stdout = f

#os.environ['HTTP_PROXY'] = ''
#os.environ['HTTPS_PROXY'] = ''

from kiosk import app as application
