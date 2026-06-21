import os
import re
import json
import logging

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'data.json')

DEFAULT_DB = {
    "glassammelaktionen": [],
    "unternehmen": [],
    "event_partner_relation": [],
    "ansprechpartner": [],
    "medienberichte": [],
    "marketing_colabs": [],
    "mediendateien": []
}

class BasePersistence:
    @staticmethod
    def parse_json(raw_json_string):
        """Entfernt fehlerhafte, abschließende Kommata vor schließenden Klammern."""
        cleaned_string = re.sub(r',\s*([\]}])', r'\1', raw_json_string)
        cleaned_string = re.sub(r',\s*$', '', cleaned_string)
        return json.loads(cleaned_string)

    @classmethod
    def load_db(cls):
        """Lädt den relationalen Datenbestand aus dem Dateisystem."""
        if not os.path.exists(DATA_FILE):
            logging.warning(f"data.json nicht unter {DATA_FILE} gefunden. Initialisiere Default-Struktur.")
            return dict(DEFAULT_DB)
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return cls.parse_json(f.read())
        except Exception as e:
            logging.error(f"Fehler beim Laden der data.json: {e}")
            return dict(DEFAULT_DB)

    @classmethod
    def save_db(cls, db_data):
        """Sichert den aktuellen Speicherzustand atomar in der data.json."""
        try:
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(db_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Fehler beim Speichern der data.json: {e}")
            return False