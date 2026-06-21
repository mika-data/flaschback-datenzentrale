from models.base import BasePersistence

class MarketingModel:
    @classmethod
    def get_colabs_by_event(cls, event_id):
        db = BasePersistence.load_db()
        return [x for x in db.get("marketing_colabs", []) if x.get("fbEventId") == event_id]

    @classmethod
    def get_media_by_event(cls, event_id):
        db = BasePersistence.load_db()
        return [x for x in db.get("mediendateien", []) if x.get("fbEventId") == event_id]

    @classmethod
    def get_news_by_event(cls, event_id):
        db = BasePersistence.load_db()
        return [x for x in db.get("medienberichte", []) if x.get("fbEventId") == event_id]