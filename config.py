import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'guild2-reforged-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///guild2_reforged.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GITLAB_URL = os.environ.get('GITLAB_URL', 'https://gitlab.com')
    GITLAB_API_TOKEN = os.environ.get('GITLAB_API_TOKEN')
    GITLAB_PROJECT_ID = os.environ.get('GITLAB_PROJECT_ID', 'fajeth-modpack/megamodpack-reforged')