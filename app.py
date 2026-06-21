import os
import re
import json
import io
import logging
import zipfile
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, Blueprint
from models import BasePersistence, SammelaktionModel, OrganisationModel
from controllers import action_controller, master_controller

# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'flaschback-datenzentrum-app.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Blueprints registrieren (Controller Isolation)
app.register_blueprint(action_controller)
app.register_blueprint(master_controller)

# -----------------------------------------------------------------------------
# CONSTANTS & DEFAULT SYSTEM VALUES (Null-Records)
# -----------------------------------------------------------------------------
DEFAULT_DB = {
    "glassammelaktionen": [
        {"fbEventId": "CGN-2026-0000", "name": "noch nicht definiert", "beschreibung": "Standard-Fallback", "datum": "2026-01-01", "ort": "Köln", "stadtteil": "Zentrum", "modus": "stationär", "dauer": "1 Tag", "lat": 50.9375, "lon": 6.9603}
    ],
    "unternehmen": [
        {"CompanyId": "COMP-0000", "Name": "noch nicht definiert", "URL": "https://koeln.de", "Rolle": "keine", "Type": "Unternehmen", "Rechtsform": "GmbH"}
    ],
    "event_partner_relation": [
        {"fbEventId": "CGN-2026-0000", "CompanyId": "COMP-0000"}
    ],
    "ansprechpartner": [
        {"ContactId": "CONT-0000", "Vorname": "nicht", "Nachname": "definiert", "Rolle": "Standard-Kontakt", "primary_organization_id": "COMP-0000", "Email": "info@koeln.de", "Handynummer": "", "Website": ""}
    ],
    "medienberichte": [
        {"NewsId": "NEWS-0000", "Headline": "Standard", "Überschrift": "Standard", "Stimmung": "neutral", "Datum": "2026-01-01", "Herausgeber": "System", "Autor": "System", "URL": "", "Fläschbäck_Zitat": "", "fbEventId": "CGN-2026-0000"}
    ],
    "marketing_colabs": [
        {"MarketingAccountId": "MARK-0000", "Account": "@standard", "Plattform": "Instagram", "ContactId": "CONT-0000", "CompanyId": "COMP-0000", "URL": "", "Zeitpunkt": "2026-01-01T00:00:00", "PostText": "", "CoAuthors": ""}
    ],
    "mediendateien": [
        {"MedienId": "MED-0000", "MedienTyp": "Foto", "Dateiformat": "jpg", "URL": "", "Dateigröße": "0KB", "Dimensionen": "0x0", "Autor": "System", "Copyright": "System", "fbEventId": "CGN-2026-0000", "Datum": "2026-01-01", "Ort": "Köln", "Lat": 50.9375, "Lon": 6.9603}
    ]
}

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'data.json')

# Sicherstellen, dass das Datenverzeichnis existiert
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

""" # -----------------------------------------------------------------------------
# CONTROLLER LAYER (Blueprints & REST-API Endpunkte)
# -----------------------------------------------------------------------------
api = Blueprint('api', __name__, url_prefix='/api/v1')

@api.route('/sammelaktionen', methods=['GET'])
def get_sammelaktionen():
    db = BasePersistence.load_db()
    return jsonify(db.get("glassammelaktionen", []))

@api.route('/sammelaktionen', methods=['POST'])
def upsert_sammelaktionen_bulk():
    db = BasePersistence.load_db()
    req_data = request.json or []
    for item in req_data:
        if "fbEventId" in item:
            item["fbEventId"] = FlaschbackModel.normalize_event_id(item["fbEventId"])
            # Upsert Logik
            existing = next((x for x in db["glassammelaktionen"] if x["fbEventId"] == item["fbEventId"]), None)
            if existing:
                existing.update(item)
            else:
                db["glassammelaktionen"].append(item)
    BasePersistence.save_db(db)
    return jsonify({"status": "Erfolg", "anzahl": len(req_data)})

@api.route('/sammelaktion/<id>', methods=['GET'])
def get_sammelaktion(id):
    db = BasePersistence.load_db()
    norm_id = SammelaktionModel.normalize_id(id)
    action = next((x for x in db.get("glassammelaktionen", []) if x["fbEventId"] == norm_id), None)
    if action:
        return jsonify(action)
    return jsonify({"fehler": "Nicht gefunden"}), 404

@api.route('/sammelaktion/<id>', methods=['POST'])
def upsert_sammelaktion(id):
    db = BasePersistence.load_db()
    norm_id = SammelaktionModel.normalize_id(id)
    item = request.json or {}
    item["fbEventId"] = norm_id
    
    existing = next((x for x in db["glassammelaktionen"] if x["fbEventId"] == norm_id), None)
    if existing:
        existing.update(item)
    else:
        db["glassammelaktionen"].append(item)
        
    BasePersistence.save_db(db)
    return jsonify({"status": "Erfolg", "fbEventId": norm_id})

@api.route('/sammelaktion/<id>', methods=['DELETE'])
def delete_sammelaktion(id):
    db = BasePersistence.load_db()
    norm_id = SammelaktionModel.normalize_id(id)
    initial_len = len(db["glassammelaktionen"])
    db["glassammelaktionen"] = [x for x in db["glassammelaktionen"] if x["fbEventId"] != norm_id]
    if len(db["glassammelaktionen"]) < initial_len:
        BasePersistence.save_db(db)
        return jsonify({"status": "Gelöscht"})
    return jsonify({"fehler": "Nicht gefunden"}), 404

@api.route('/organisationen', methods=['GET'])
def get_organisationen():
    db = BasePersistence.load_db()
    return jsonify(db.get("unternehmen", []))

@api.route('/organisationen', methods=['POST'])
def upsert_organisationen_bulk():
    db = BasePersistence.load_db()
    req_data = request.json or []
    for item in req_data:
        if "CompanyId" in item:
            existing = next((x for x in db["unternehmen"] if x["CompanyId"] == item["CompanyId"]), None)
            if existing:
                existing.update(item)
            else:
                db["unternehmen"].append(item)
    BasePersistence.save_db(db)
    return jsonify({"status": "Erfolg", "anzahl": len(req_data)})

@api.route('/relation', methods=['POST'])
def create_relation():
    db = BasePersistence.load_db()
    req = request.json or {}
    fb_id = SammelaktionModel.normalize_id(req.get("fbEventId"))
    comp_id = req.get("CompanyId")
    if fb_id and comp_id:
        exists = any(x for x in db["event_partner_relation"] if x["fbEventId"] == fb_id and x["CompanyId"] == comp_id)
        if not exists:
            db["event_partner_relation"].append({"fbEventId": fb_id, "CompanyId": comp_id})
            BasePersistence.save_db(db)
        return jsonify({"status": "Relation verknüpft"})
    return jsonify({"fehler": "Ungültige Parameter"}), 400

@api.route('/export', methods=['GET'])
def export_zip():
    db = BasePersistence.load_db()
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # data.json hinzufügen
        json_data = json.dumps(db, indent=2, ensure_ascii=False)
        zf.writestr('data.json', json_data)
        # Leeres Medienverzeichnis erzeugen
        zf.writestr('medien/', '')
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='flaeschbaeck_master.zip')

@api.route('/import', methods=['POST'])
def import_data():
    if 'file' not in request.files:
        return jsonify({"fehler": "Keine Datei hochgeladen"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"fehler": "Leerer Dateiname"}), 400

    try:
        if file.filename.endswith('.zip'):
            with zipfile.ZipFile(file) as zf:
                if 'data.json' not in zf.namelist():
                    return jsonify({"fehler": "Keine data.json im ZIP-Archiv gefunden"}), 400
                raw_content = zf.read('data.json').decode('utf-8')
        else:
            raw_content = file.read().decode('utf-8')

        parsed_data = BasePersistence.parse_json(raw_content)
        
        # Validierung der Pflicht-Keys
        for key in DEFAULT_DB.keys():
            if key not in parsed_data:
                parsed_data[key] = list(DEFAULT_DB[key])
                
        BasePersistence.save_db(parsed_data)
        return jsonify({"status": "Erfolg", "nachricht": "Daten erfolgreich importiert und validiert"})
    except Exception as e:
        return jsonify({"fehler": f"Fehler beim Parsen/Importieren: {str(e)}"}), 400

app.register_blueprint(api)
 """
# -----------------------------------------------------------------------------
# VIEW LAYER (Base Server Render Routing & Templates)
# -----------------------------------------------------------------------------
@app.route('/')
def dashboard():
    db = BasePersistence.load_db()
    return render_template('dashboard.html', db=db)

if __name__ == '__main__':
    # Initialer Datencheck und Vorladen der echten Master-Daten falls vorhanden
    print("🚀 Fläschbäck-Datenzentrale wird gestartet...")
    #app.run(debug=True, host='0.0.0.0', port=5000, ssl_context='adhoc' )
    app.run(debug=True, port=5000 )
