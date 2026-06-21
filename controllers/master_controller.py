import io
import zipfile
import json
import logging
from flask import Blueprint, jsonify, request, send_file
from models.base import BasePersistence, DEFAULT_DB
from models.organisation import OrganisationModel

master_controller = Blueprint('master_controller', __name__, url_prefix='/api/v1')

@master_controller.route('/organisationen', methods=['GET'])
def get_organisationen():
    logging.info("API Trigger: GET /api/v1/organisationen")
    return jsonify(OrganisationModel.get_all())

@master_controller.route('/organisationen', methods=['POST'])
def upsert_organisationen_bulk():
    logging.info("API Trigger: POST /api/v1/organisationen (Bulk)")
    req_data = request.json or []
    for item in req_data:
        if "CompanyId" in item:
            OrganisationModel.upsert(item["CompanyId"], item)
    return jsonify({"status": "Erfolg", "anzahl": len(req_data)})

@master_controller.route('/organisation/<id>', methods=['GET'])
def get_organisation(id):
    logging.info(f"API Trigger: GET /api/v1/organisation/{id}")
    org = OrganisationModel.get_by_id(id)
    if org:
        return jsonify(org)
    return jsonify({"fehler": "Nicht gefunden"}), 404

@master_controller.route('/organisation/<id>', methods=['POST'])
def upsert_organisation(id):
    logging.info(f"API Trigger: POST /api/v1/organisation/{id}")
    item = request.json or {}
    OrganisationModel.upsert(id, item)
    return jsonify({"status": "Erfolg", "CompanyId": id})

@master_controller.route('/export', methods=['GET'])
def export_zip():
    logging.info("API Trigger: GET /api/v1/export")
    db = BasePersistence.load_db()
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        json_data = json.dumps(db, indent=2, ensure_ascii=False)
        zf.writestr('data.json', json_data)
        zf.writestr('medien/', '')
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='flaeschbaeck_master.zip')

@master_controller.route('/import', methods=['POST'])
def import_data():
    logging.info("API Trigger: POST /api/v1/import gestartet.")
    
    if 'file' not in request.files:
        logging.warning("Import-Versuch ohne Datei-Attribut abgelehnt.")
        return jsonify({"fehler": "Keine Datei im Request-Payload gefunden (Form-Data Key 'file' fehlt)"}), 400
        
    file = request.files['file']
    if file.filename == '':
        logging.warning("Import-Versuch mit leerem Dateinamen abgelehnt.")
        return jsonify({"fehler": "Dateiname darf nicht leer sein"}), 400

    try:
        # Fall 1: ZIP-Archiv entpacken und data.json extrahieren
        if file.filename.endswith('.zip'):
            logging.info(f"Verarbeite ZIP-Import: {file.filename}")
            with zipfile.ZipFile(file) as zf:
                if 'data.json' not in zf.namelist():
                    logging.error("Validierungsfehler: data.json fehlt im ZIP-Wurzelverzeichnis.")
                    return jsonify({"fehler": "Ungültiges Archiv: Keine data.json im ZIP-Archiv gefunden"}), 400
                raw_content = zf.read('data.json').decode('utf-8')
        
        # Fall 2: Reine JSON-Datei einlesen
        else:
            logging.info(f"Verarbeite native JSON-Datei: {file.filename}")
            raw_content = file.read().decode('utf-8')

        # Fehlertolerantes Parsen (Trailing Commas Regex) über das Basis-Model
        parsed_data = BasePersistence.parse_json(raw_content)
        
        # Relationale Integritätssicherung: Fehlende Keys mit Standard-Strukturen (Null-Records) auffüllen
        ergaenzte_keys = []
        for key in DEFAULT_DB.keys():
            if key not in parsed_data or not isinstance(parsed_data[key], list):
                parsed_data[key] = list(DEFAULT_DB[key])
                ergaenzte_keys.append(key)
                
        if ergaenzte_keys:
            logging.info(f"Struktur repariert. Folgende Tabellen wurden als Default initialisiert: {ergaenzte_keys}")

        # Persistent abspeichern
        BasePersistence.save_db(parsed_data)
        logging.info("Import erfolgreich validiert und in data.json geschrieben.")
        
        return jsonify({
            "status": "Erfolg",
            "nachricht": "Daten erfolgreich importiert, repariert und strukturell abgeglichen.",
            "ergaenzte_tabellen": ergaenzte_keys
        }), 200
        
    except json.JSONDecodeError as jde:
        logging.error(f"JSON-Parsing fehlgeschlagen trotz Regex-Sanitierung: {jde}")
        return jsonify({"fehler": f"Defektes JSON-Format: {str(jde)}"}), 400
    except Exception as e:
        logging.error(f"Kritischer Fehler während der Import-Pipeline: {e}")
        return jsonify({"fehler": f"Interner Verarbeitungsfehler beim Import: {str(e)}"}), 500