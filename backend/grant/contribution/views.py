from flask import Blueprint, current_app, g
from marshmallow import fields
from sentry_sdk import capture_message

from grant.contribution.models import Contribution
from grant.email.send import send_email
from grant.extensions import db
from grant.parser import body
from grant.settings import PROPOSAL_STAKING_AMOUNT, CCR_STAKING_AMOUNT
from grant.ccr.models import CCR
from grant.utils.auth import internal_webhook, requires_auth
from grant.utils.enums import ContributionStatus, ProposalStatus, CCRStatus
from grant.utils.misc import from_zat, make_explore_url, make_url

blueprint = Blueprint("contribution", __name__, url_prefix="/api/v1/contribution")


@blueprint.route("/<contribution_id>/confirm", methods=["POST"])
@internal_webhook
@body({
    "to": fields.Str(required=True),
    "amount": fields.Str(required=True),
    "txid": fields.Str(required=True),
})
def post_contribution_confirmation(contribution_id, to, amount, txid):
    contribution = Contribution.query.filter_by(
        id=contribution_id).first()

    if not contribution:
        msg = f'Unknown contribution {contribution_id} confirmed with txid {txid}, amount {amount}'
        capture_message(msg)
        current_app.logger.warn(msg)
        return {"message": "No contribution matching id"}, 404

    if contribution.status == ContributionStatus.CONFIRMED:
        # Duplicates can happen, just return ok
        return {"message": "ok"}, 200

    # Convert to whole zcash coins from zats
    zec_amount = str(from_zat(int(amount)))

    contribution.confirm(tx_id=txid, amount=zec_amount)
    db.session.add(contribution)
    db.session.flush()

    if contribution.proposal_id:
        if contribution.proposal.status == ProposalStatus.STAKING:
            contribution.proposal.set_pending_when_ready()

            # email progress of staking, partial or complete
            send_email(contribution.user.email_address, 'staking_contribution_confirmed', {
                'contribution': contribution,
                'proposal': contribution.proposal,
                'tx_explorer_url': make_explore_url(txid),
                'fully_staked': contribution.proposal.is_staked,
                'stake_target': str(PROPOSAL_STAKING_AMOUNT.normalize()),
            })

        else:
            # Send to the user
            if contribution.user:
                send_email(contribution.user.email_address, 'contribution_confirmed', {
                    'contribution': contribution,
                    'proposal': contribution.proposal,
                    'tx_explorer_url': make_explore_url(txid),
                })

            # Send to the full proposal gang
            for member in contribution.proposal.team:
                send_email(member.email_address, 'proposal_contribution', {
                    'proposal': contribution.proposal,
                    'contribution': contribution,
                    'contributor': contribution.user,
                    'funded': contribution.proposal.funded,
                    'proposal_url': make_url(f'/proposals/{contribution.proposal.id}'),
                    'contributor_url': make_url(f'/profile/{contribution.user.id}') if contribution.user else '',
                })

        db.session.commit()
        return {"message": "ok"}, 200

    if contribution.ccr_id:
        ccr = CCR.query.get(contribution.ccr_id)
        if ccr.status == CCRStatus.STAKING:
            ccr.set_pending_when_ready()

            # email progress of staking, partial or complete
            # TODO SEND EMAIL
            # send_email(contribution.user.email_address, 'staking_contribution_confirmed', {
            #     'contribution': contribution,
            #     'proposal': contribution.proposal,
            #     'tx_explorer_url': make_explore_url(txid),
            #     'fully_staked': contribution.proposal.is_staked,
            #     'stake_target': str(PROPOSAL_STAKING_AMOUNT.normalize()),
            # })

        else:
            # Send to the user
            if contribution.user:
                pass
                # TODO
                # send_email(contribution.user.email_address, 'contribution_confirmed', {
                #     'contribution': contribution,
                #     'proposal': contribution.proposal,
                #     'tx_explorer_url': make_explore_url(txid),
                # })

        db.session.commit()
        return {"message": "ok"}, 200

    # TODO log error, respond 400 if get here


@blueprint.route("/<contribution_id>", methods=["DELETE"])
@requires_auth
def delete_proposal_contribution(contribution_id):
    contribution = Contribution.query.filter_by(
        id=contribution_id).first()
    if not contribution:
        return {"message": "No contribution matching id"}, 404

    if contribution.status == ContributionStatus.CONFIRMED:
        return {"message": "Cannot delete confirmed contributions"}, 400

    if contribution.user_id != g.current_user.id:
        return {"message": "Must be the user of the contribution to delete it"}, 403

    contribution.status = ContributionStatus.DELETED
    db.session.add(contribution)
    db.session.commit()
    return {"message": "ok"}, 202
