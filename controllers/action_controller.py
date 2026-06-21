import logging
from flask import Blueprint, jsonify, request
from models.sammelaktion import SammelaktionModel

action_controller = Blueprint('action_controller', __name__, url_prefix='/api/v1')

@action_controller.route('/sammelaktionen', methods=['GET'])
def get_sammelaktionen():
    logging.info("API Trigger: GET /api/v1/sammelaktionen")
    return jsonify(SammelaktionModel.get_all())

@action_controller.route('/sammelaktionen', methods=['POST'])
def upsert_sammelaktionen_bulk():
    logging.info("API Trigger: POST /api/v1/sammelaktionen (Bulk)")
    req_data = request.json or []
    for item in req_data:
        if "fbEventId" in item:
            SammelaktionModel.upsert(item["fbEventId"], item)
    return jsonify({"status": "Erfolg", "anzahl": len(req_data)})

@action_controller.route('/sammelaktion/<id>', methods=['GET'])
def get_sammelaktion(id):
    logging.info(f"API Trigger: GET /api/v1/sammelaktion/{id}")
    action = SammelaktionModel.get_by_id(id)
    if action:
        return jsonify(action)
    return jsonify({"fehler": "Nicht gefunden"}), 404

@action_controller.route('/sammelaktion/<id>', methods=['POST'])
def upsert_sammelaktion(id):
    logging.info(f"API Trigger: POST /api/v1/sammelaktion/{id} (Upsert)")
    item = request.json or {}
    norm_id = SammelaktionModel.upsert(id, item)
    return jsonify({"status": "Erfolg", "fbEventId": norm_id})

@action_controller.route('/sammelaktion/<id>', methods=['DELETE'])
def delete_sammelaktion(id):
    logging.info(f"API Trigger: DELETE /api/v1/sammelaktion/{id}")
    if SammelaktionModel.delete(id):
        return jsonify({"status": "Gelöscht"})
    return jsonify({"fehler": "Nicht gefunden"}), 404

@action_controller.route('/relation', methods=['POST'])
def create_relation():
    logging.info("API Trigger: POST /api/v1/relation")
    req = request.json or {}
    fb_id = req.get("fbEventId")
    comp_id = req.get("CompanyId")
    if fb_id and comp_id:
        if SammelaktionModel.add_partner_relation(fb_id, comp_id):
            return jsonify({"status": "Relation verknüpft"})
        return jsonify({"status": "Relation existierte bereits"})
    return jsonify({"fehler": "Ungültige Parameter"}), 400