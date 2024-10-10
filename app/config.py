from zoneinfo import ZoneInfo

class Config:
    SECONDS_PER_HOUR = 3600
    TIMEZONE = 'Asia/Karachi'

    @staticmethod
    def get_timezone():
        return ZoneInfo(Config.TIMEZONE)
