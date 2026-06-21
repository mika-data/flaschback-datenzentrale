import io
import zipfile
import json
import logging
from flask import Blueprint, jsonify, request, send_file
from models.base import BasePersistence
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
    logging.info("API Trigger: POST /api/v1/import")
    if 'file' not in request.files:
        return jsonify({"fehler": "Keine Datei hochgeladen"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"fehler": "Leerer Dateiname"}), 400

    try:
        if file.filename.endswith('.zip'):
            with zipfile.ZipFile(file) as zf:
                if 'data.json' not in zf.namelist():
                    return jsonify({"fehler": "Keine data.json im ZIP-Archiv"}), 400
                raw_content = zf.read('data.json').decode('utf-8')
        else:
            raw_content = file.read().decode('utf-8')

        parsed_data = BasePersistence.parse_json(raw_content)
        BasePersistence.save_db(parsed_data)
        return jsonify({"status": "Erfolg", "nachricht": "Daten erfolgreich importiert"})
    except Exception as e:
        logging.error(f"Import fehlgeschlagen: {e}")
        return jsonify({"fehler": f"Fehler beim Import: {str(e)}"}), 400