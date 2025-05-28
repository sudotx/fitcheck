from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Fit

fit_bp = Blueprint("fit", __name__)


@fit_bp.route("/fits", methods=["POST"])
@jwt_required()
def create_fit():
    data = request.get_json()
    name = data.get("name")
    user_id = get_jwt_identity()

    if not name:
        return jsonify({"error": "Name is required"}), 400

    fit = Fit(name=name, user_id=user_id)
    db.session.add(fit)
    db.session.commit()

    return jsonify({"message": "Fit created successfully", "fit_id": fit.id}), 201


@fit_bp.route("/fits/<string:fit_id>", methods=["GET"])
@jwt_required()
def get_fit(fit_id):
    fit = Fit.query.get_or_404(fit_id)
    return jsonify({"id": fit.id, "name": fit.name, "user_id": fit.user_id}), 200


@fit_bp.route("/fits", methods=["GET"])
@jwt_required()
def get_user_fits():
    user_id = get_jwt_identity()
    fits = Fit.query.filter_by(user_id=user_id).all()
    return (
        jsonify(
            [{"id": fit.id, "name": fit.name, "user_id": fit.user_id} for fit in fits]
        ),
        200,
    )
