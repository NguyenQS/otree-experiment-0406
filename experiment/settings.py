from os import environ

SESSION_CONFIGS = [
    dict(
        name='combined_task',              # Name frei wählbar
        app_sequence=['experiment'],       # nur deine neue App hier!
        num_demo_participants=1,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """
SECRET_KEY = 'deine_geheime_key'

INSTALLED_APPS = ['otree']
