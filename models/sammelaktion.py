
from models.base import BasePersistence

class SammelaktionModel:
    @staticmethod
    def normalize_id(id_str):
        """Normalisiert die Event-ID auf ein vierstelliges Suffix (z.B. CGN-2026-0001)."""
        if not id_str or not isinstance(id_str, str):
            return id_str
        parts = id_str.split('-')
        if len(parts) >= 3 and parts[-1].isdigit():
            parts[-1] = parts[-1].zfill(4)
            return "-".join(parts)
        return id_str

    @classmethod
    def get_all(cls):
        db = BasePersistence.load_db()
        return db.get("glassammelaktionen", [])

    @classmethod
    def get_by_id(cls, event_id):
        norm_id = cls.normalize_id(event_id)
        actions = cls.get_all()
        return next((x for x in actions if x.get("fbEventId") == norm_id), None)

    @classmethod
    def upsert(cls, event_id, data):
        """Führt ein Update oder Insert für eine Sammelaktion durch."""
        db = BasePersistence.load_db()
        norm_id = cls.normalize_id(event_id)
        data["fbEventId"] = norm_id
        
        existing_index = next((i for i, x in enumerate(db["glassammelaktionen"]) if x["fbEventId"] == norm_id), None)
        if existing_index is not None:
            db["glassammelaktionen"][existing_index].update(data)
        else:
            db["glassammelaktionen"].append(data)
            
        BasePersistence.save_db(db)
        return norm_id

    @classmethod
    def delete(cls, event_id):
        db = BasePersistence.load_db()
        norm_id = cls.normalize_id(event_id)
        initial_count = len(db["glassammelaktionen"])
        db["glassammelaktionen"] = [x for x in db["glassammelaktionen"] if x["fbEventId"] != norm_id]
        
        if len(db["glassammelaktionen"]) < initial_count:
            BasePersistence.save_db(db)
            return True
        return False

    @classmethod
    def add_partner_relation(cls, event_id, company_id):
        """Erstellt eine relationale Zuordnung in der n:m Verknüpfungstabelle."""
        db = BasePersistence.load_db()
        norm_id = cls.normalize_id(event_id)
        
        exists = any(x for x in db["event_partner_relation"] if x["fbEventId"] == norm_id and x["CompanyId"] == company_id)
        if not exists:
            db["event_partner_relation"].append({"fbEventId": norm_id, "CompanyId": company_id})
            BasePersistence.save_db(db)
            return True
        return False