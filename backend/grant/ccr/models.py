from datetime import datetime
from decimal import Decimal
from functools import reduce

from sqlalchemy.ext.hybrid import hybrid_property

from grant.email.send import send_email
from grant.extensions import ma, db
from grant.settings import CCR_STAKING_AMOUNT
from grant.utils.enums import CCRStatus
from grant.utils.enums import (
    ContributionStatus
)
from grant.task.jobs import ContributionExpired

from grant.utils.exceptions import ValidationException
from grant.utils.misc import dt_to_unix, make_admin_url, gen_random_id
from grant.utils.requests import blockchain_get
from grant.contribution.models import Contribution


class CCR(db.Model):
    __tablename__ = "ccr"

    id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.DateTime)

    title = db.Column(db.String(255), nullable=True)
    brief = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(255), nullable=False)
    _target = db.Column("target", db.String(255), nullable=True)
    reject_reason = db.Column(db.String())

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    author = db.relationship("User", back_populates="ccrs")

    @hybrid_property
    def is_staked(self):
        contributions = Contribution.query \
            .filter_by(ccr_id=self.id,
                       status=ContributionStatus.CONFIRMED) \
            .all()
        funded = reduce(lambda prev, c: prev + Decimal(c.amount), contributions, 0)
        return Decimal(funded) >= CCR_STAKING_AMOUNT

    @staticmethod
    def create(**kwargs):
        ccr = CCR(
            **kwargs
        )

        db.session.add(ccr)
        db.session.flush()

        return ccr

    @hybrid_property
    def target(self):
        return self._target

    @target.setter
    def target(self, target: str):
        if target and Decimal(target) > 0:
            self._target = target
        else:
            self._target = None

    def __init__(
            self,
            user_id: int,
            title: str = '',
            brief: str = '',
            content: str = '',
            target: str = '0',
            status: str = CCRStatus.DRAFT,
    ):
        assert CCRStatus.includes(status)
        self.id = gen_random_id(CCR)
        self.date_created = datetime.now()
        self.title = title[:255]
        self.brief = brief[:255]
        self.content = content
        self.target = target
        self.status = status
        self.user_id = user_id

    def update(
            self,
            title: str = '',
            brief: str = '',
            content: str = '',
            target: str = '0',
    ):
        self.title = title[:255]
        self.brief = brief[:255]
        self.content = content[:300000]
        self._target = target[:255] if target != '' else '0'

    # state: status (DRAFT || REJECTED) -> (PENDING || STAKING)
    def submit_for_approval(self):
        # TODO validate user generated content
        # self.validate_publishable()
        allowed_statuses = [CCRStatus.DRAFT, CCRStatus.REJECTED]
        # specific validation
        if self.status not in allowed_statuses:
            raise ValidationException(f"CCR status must be draft or rejected to submit for approval")
        # set to PENDING if staked, else STAKING
        if self.is_staked:
            self.status = CCRStatus.PENDING
        else:
            self.status = CCRStatus.STAKING

    def set_pending_when_ready(self):
        if self.status == CCRStatus.STAKING and self.is_staked:
            self.set_pending()

    def create_contribution(
        self,
        amount,
        user_id: int = None,
        staking: bool = False,
    ):
        contribution = Contribution(
            ccr_id=self.id,
            amount=amount,
            user_id=user_id,
            staking=staking,
        )
        db.session.add(contribution)
        db.session.flush()
        if user_id:
            task = ContributionExpired(contribution)
            task.make_task()
        db.session.commit()
        return contribution

    def get_staking_contribution(self, user_id: int):
        contribution = None
        remaining = CCR_STAKING_AMOUNT - Decimal(self.amount_staked)
        # check funding
        if remaining > 0:
            # find pending contribution for any user of remaining amount
            contribution = Contribution.query.filter_by(
                ccr_id=self.id,
                status=CCRStatus.PENDING,
                staking=True,
            ).first()
            if not contribution:
                contribution = self.create_contribution(
                    user_id=user_id,
                    amount=str(remaining.normalize()),
                    staking=True,
                )

        return contribution

    @hybrid_property
    def amount_staked(self):
        contributions = Contribution.query.filter_by(
            ccr_id=self.id,
            status=ContributionStatus.CONFIRMED,
            staking=True
        ).all()
        amount = reduce(lambda prev, c: prev + Decimal(c.amount), contributions, 0)
        return str(amount)

    def send_admin_email(self, type: str):
        from grant.user.models import User
        admins = User.get_admins()
        for a in admins:
            send_email(a.email_address, type, {
                'user': a,
                'ccr': self,
                'ccr_url': make_admin_url(f'/ccrs/{self.id}'),
            })

    # state: status STAKING -> PENDING
    def set_pending(self):
        if self.status != CCRStatus.STAKING:
            raise ValidationException(f"CCR status must be staking in order to be set to pending")
        if not self.is_staked:
            raise ValidationException(f"CCR is not fully staked, cannot set to pending")
        self.send_admin_email('admin_approval_ccr')
        self.status = CCRStatus.PENDING
        db.session.add(self)
        db.session.flush()

    # state: status PENDING -> (LIVE || REJECTED)
    def approve_pending(self, is_approve, reject_reason=None):
        self.validate_publishable()
        # specific validation
        if not self.status == CCRStatus.PENDING:
            raise ValidationException(f"CCR must be pending to approve or reject")

        if is_approve:
            self.status = CCRStatus.LIVE
            # TODO make into rfp and set to live

            # TODO email notify that CCR was accepted
            # send_email(t.email_address, 'ccr_approved', {
            #     'user': t,
            #     'ccr': self,
            #     'ccr_url': make_url(f'/ccrs/{self.id}'),
            #     'admin_note': f'Congratulations! Your Request has been accepted. .'
            # })
        else:
            if not reject_reason:
                raise ValidationException("Please provide a reason for rejecting the ccr")
            self.status = CCRStatus.REJECTED
            self.reject_reason = reject_reason
            # email that CCR was rejected
            # send_email(t.email_address, 'ccr_rejected', {
            #     'user': t,
            #     'ccr': self,
            #     'ccr_url': make_url(f'/ccrs/{self.id}'),
            #     'admin_note': reject_reason
            # })


class CCRSchema(ma.Schema):
    class Meta:
        model = CCR
        # Fields to expose
        fields = (
            "author",
            "id",
            "title",
            "brief",
            "ccr_id",
            "content",
            "status",
            "target",
            "date_created",
            "is_staked",
            "reject_reason"
        )

    author = ma.Nested("UserSchema")
    ccr_id = ma.Method("get_ccr_id")

    def get_ccr_id(self, obj):
        return obj.id


ccr_schema = CCRSchema()
ccrs_schema = CCRSchema(many=True)


class CCRContributionSchema(ma.Schema):
    class Meta:
        model = Contribution
        # Fields to expose
        fields = (
            "id",
            "ccr",
            "user",
            "status",
            "tx_id",
            "amount",
            "date_created",
            "addresses",
            "private"
        )

    ccr = ma.Nested("CCRSchema")
    user = ma.Nested("UserSchema")
    date_created = ma.Method("get_date_created")
    addresses = ma.Method("get_addresses")

    def get_date_created(self, obj):
        return dt_to_unix(obj.date_created)

    def get_addresses(self, obj):
        # Omit 'memo' and 'sprout' for now
        # NOTE: Add back in 'sapling' when ready
        addresses = blockchain_get('/contribution/addresses', {'contributionId': obj.id})
        return {
            'transparent': addresses['transparent'],
        }


ccr_contribution_schema = CCRContributionSchema()
ccr_contributions_schema = CCRContributionSchema(many=True)
