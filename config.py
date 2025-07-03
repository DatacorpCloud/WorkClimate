import os

class Config:
    # Configurazione generale
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chiave_segreta_da_cambiare_in_produzione'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///worklimate.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurazione per l'invio di email
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Configurazione per lo scheduler
    SCHEDULER_API_ENABLED = True

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # In produzione, assicurarsi di impostare una SECRET_KEY sicura
    # e utilizzare un database più robusto come PostgreSQL o MySQL

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}