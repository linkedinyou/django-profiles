# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_assets', # for assets minification
    'sekizai', # to extend scripts and styles organization

    'profiles', # common profiles application
    'bootstrap3', # for bootstraping forms
)
