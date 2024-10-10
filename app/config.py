from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient
from app.main import app 

class Config:
    SECONDS_PER_HOUR = 3600
    TIMEZONE = 'Asia/Karachi'
    client = TestClient(app)


    @staticmethod
    def get_timezone():
        return ZoneInfo(Config.TIMEZONE)
