from models.base import BasePersistence

class OrganisationModel:
    @classmethod
    def get_all(cls):
        db = BasePersistence.load_db()
        return db.get("unternehmen", [])

    @classmethod
    def get_by_id(cls, company_id):
        companies = cls.get_all()
        return next((x for x in companies if x.get("CompanyId") == company_id), None)

    @classmethod
    def upsert(cls, company_id, data):
        db = BasePersistence.load_db()
        data["CompanyId"] = company_id
        
        existing_index = next((i for i, x in enumerate(db["unternehmen"]) if x["CompanyId"] == company_id), None)
        if existing_index is not None:
            db["unternehmen"][existing_index].update(data)
        else:
            db["unternehmen"].append(data)
            
        BasePersistence.save_db(db)
        return company_id

    @classmethod
    def get_contacts_by_organisation(cls, company_id):
        """Liefert alle Kontakte, deren primary_organization_id der CompanyId entspricht."""
        db = BasePersistence.load_db()
        return [x for x in db.get("ansprechpartner", []) if x.get("primary_organization_id") == company_id]