import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Client

from app.core.config import settings

def init_firebase() -> None:
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        firebase_admin.initialize_app(cred)

def get_firestore_client() -> Client:
    return firestore.client()
