import datetime
from _pydecimal import Decimal

from sqlalchemy.ext.hybrid import hybrid_property

from grant.extensions import db
from grant.utils.enums import ContributionStatus
from grant.utils.exceptions import ValidationException


class Contribution(db.Model):
    __tablename__ = "proposal_contribution"

    id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False)
    ccr_id = db.Column(db.Integer, db.ForeignKey("ccr.id"), nullable=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposal.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    status = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.String(255), nullable=False)
    tx_id = db.Column(db.String(255), nullable=True)
    refund_tx_id = db.Column(db.String(255), nullable=True)
    staking = db.Column(db.Boolean, nullable=False)
    private = db.Column(db.Boolean, nullable=False, default=False, server_default='true')

    user = db.relationship("User")

    def __init__(
            self,
            amount: str,
            ccr_id: int = None,
            proposal_id: int = None,
            user_id: int = None,
            staking: bool = False,
            private: bool = True,
    ):
        if not ccr_id and not proposal_id:
            raise ValidationException("Either ccr id or proposal id is required")
        if ccr_id and proposal_id:
            raise ValidationException("Can't relate a contribution to both a proposal and a ccr")
        self.ccr_id = ccr_id
        self.proposal_id = proposal_id
        self.amount = amount
        self.user_id = user_id
        self.staking = staking
        self.private = private
        self.date_created = datetime.datetime.now()
        self.status = ContributionStatus.PENDING

    @staticmethod
    def get_existing_ccr_contribution(user_id: int, ccr_id: int, amount: str, private: bool = False):
        return Contribution.query.filter_by(
            user_id=user_id,
            ccr_id=ccr_id,
            amount=amount,
            private=private,
            status=ContributionStatus.PENDING,
        ).first()

    @staticmethod
    def get_ccr_contribution_by_userid(user_id):
        return Contribution.query \
            .filter(Contribution.user_id == user_id) \
            .filter(Contribution.status != ContributionStatus.DELETED) \
            .filter(Contribution.staking == False) \
            .filter(Contribution.ccr_id is not None) \
            .order_by(Contribution.date_created.desc()) \
            .all()

    @staticmethod
    def get_existing_proposal_contribution(user_id: int, proposal_id: int, amount: str, private: bool = False):
        return Contribution.query.filter_by(
            user_id=user_id,
            proposal_id=proposal_id,
            amount=amount,
            private=private,
            status=ContributionStatus.PENDING,
        ).first()

    @staticmethod
    def get_proposal_contributions_by_userid(user_id):
        return Contribution.query \
            .filter(Contribution.user_id == user_id) \
            .filter(Contribution.status != ContributionStatus.DELETED) \
            .filter(Contribution.staking == False) \
            .filter(Contribution.proposal_id is not None) \
            .order_by(Contribution.date_created.desc()) \
            .all()

    @staticmethod
    def base_validate(contribution):
        user_id = contribution.get('user_id')
        status = contribution.get('status')
        amount = contribution.get('amount')
        tx_id = contribution.get('tx_id')

        # User ID (must belong to an existing user)
        if user_id:
            from grant.user.models import User

            user = User.query.filter(User.id == user_id).first()
            if not user:
                raise ValidationException('No user matching that ID')
            contribution.user_id = user_id
        else:
            raise ValidationException('User ID is required')
        # Status (must be in list of statuses)
        if status:
            if not ContributionStatus.includes(status):
                raise ValidationException('Invalid status')
            contribution.status = status
        else:
            raise ValidationException('Status is required')
        # Amount (must be a Decimal parseable)
        if amount:
            try:
                contribution.amount = str(Decimal(amount))
            except:
                raise ValidationException('Amount must be a number')
        else:
            raise ValidationException('Amount is required')

    @staticmethod
    def validate_proposal(contribution):
        from grant.proposal.models import Proposal
        Contribution.base_validate(contribution)
        proposal_id = contribution.get('proposal_id')
        # Proposal ID (must belong to an existing proposal)
        if proposal_id:
            proposal = Proposal.query.filter(Proposal.id == proposal_id).first()
            if not proposal:
                raise ValidationException('No proposal matching that ID')
            contribution.proposal_id = proposal_id
        else:
            raise ValidationException('Proposal ID is required')

    @staticmethod
    def validate_ccr(contribution):
        from grant.ccr.models import CCR
        Contribution.base_validate(contribution)
        ccr_id = contribution.get('ccr_id')
        if ccr_id:
            ccr = CCR.query.filter(CCR.id == ccr_id).first()
            if not ccr:
                raise ValidationException('No ccr matching that ID')
            contribution.ccr_id = ccr_id
        else:
            raise ValidationException('CCR ID is required')

    def confirm(self, tx_id: str, amount: str):
        self.status = ContributionStatus.CONFIRMED
        self.tx_id = tx_id
        self.amount = amount

    @hybrid_property
    def refund_address(self):
        return self.user.settings.refund_address if self.user else None