from flask import Blueprint, g
from marshmallow import fields
from sqlalchemy import or_

from grant.extensions import limiter
from grant.parser import body
from grant.utils.auth import (
    requires_auth,
    requires_email_verified_auth
)
from grant.utils.auth import requires_ccr_owner_auth
from grant.utils.enums import CCRStatus
from grant.utils.exceptions import ValidationException
from .models import CCR, ccr_schema, ccrs_schema, db

blueprint = Blueprint("ccr", __name__, url_prefix="/api/v1/ccrs")


@blueprint.route("/drafts", methods=["POST"])
@limiter.limit("10/hour;3/minute")
@requires_email_verified_auth
def make_ccr_draft():
    user = g.current_user
    ccr = CCR.create(status=CCRStatus.DRAFT, user_id=user.id)
    return ccr_schema.dump(ccr), 201


@blueprint.route("/drafts", methods=["GET"])
@requires_auth
def get_proposal_drafts():
    ccrs = (
        CCR.query
            .filter(or_(
            CCR.status == CCRStatus.DRAFT,
            CCR.status == CCRStatus.REJECTED,
        ))
            .order_by(CCR.date_created.desc())
            .all()
    )
    return ccrs_schema.dump(ccrs), 200


@blueprint.route("/<ccr_id>", methods=["PUT"])
@requires_ccr_owner_auth
@body({
    "title": fields.Str(required=True),
    "brief": fields.Str(required=True),
    "content": fields.Str(required=True),
    "bounty": fields.Str(required=True),
})
def update_ccr(ccr_id, **kwargs):
    try:
        if g.current_ccr.status not in [CCRStatus.DRAFT,
                                        CCRStatus.REJECTED]:
            raise ValidationException(
                f"CCR with status: {g.current_ccr.status} are not authorized for updates"
            )
        g.current_ccr.update(**kwargs)
    except ValidationException as e:
        return {"message": "{}".format(str(e))}, 400
    db.session.add(g.current_ccr)

    # Commit
    db.session.commit()
    return ccr_schema.dump(g.current_ccr), 200


@blueprint.route("/<ccr_id>/like", methods=["PUT"])
@requires_auth
@body({"isLiked": fields.Bool(required=True)})
def like_ccr(ccr_id, is_liked):
    user = g.current_user
    # Make sure rfp exists
    ccr = CCR.query.filter_by(id=ccr_id).first()
    if not ccr:
        return {"message": "No CCR matching id"}, 404
    if not ccr.status == CCRStatus.LIVE:
        return {"message": "CCR is not live"}, 404

    ccr.like(user, is_liked)
    db.session.commit()
    return {"message": "ok"}, 200

# @blueprint.route("/<ccr_id>/submit_for_approval", methods=["PUT"])
# def submit_for_approval_proposal(ccr_id):
# try:
#     g.current_proposal.submit_for_approval()
# except ValidationException as e:
#     return {"message": "{}".format(str(e))}, 400
# db.session.add(g.current_proposal)
# db.session.commit()
# return proposal_schema.dump(g.current_proposal), 200
