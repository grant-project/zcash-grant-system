import datetime
from decimal import Decimal, ROUND_DOWN
from functools import reduce

from flask import current_app
from marshmallow import post_dump
from sqlalchemy import func, or_
from sqlalchemy.ext.hybrid import hybrid_property

from flask import current_app
from grant.comment.models import Comment
from grant.email.send import send_email
from grant.extensions import ma, db
from grant.utils.enums import (
    ProposalStatus,
    ProposalStage,
    Category,
    ProposalArbiterStatus,
    MilestoneStage
)
from grant.utils.exceptions import ValidationException
from grant.utils.misc import dt_to_unix, make_url, make_admin_url, gen_random_id
from grant.utils.requests import blockchain_get
from grant.utils.stubs import anonymous_user

proposal_team = db.Table(
    'proposal_team', db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('proposal_id', db.Integer, db.ForeignKey('proposal.id'))
)


class ProposalTeamInvite(db.Model):
    __tablename__ = "proposal_team_invite"

    id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.DateTime)

    proposal_id = db.Column(db.Integer, db.ForeignKey("proposal.id"), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    accepted = db.Column(db.Boolean)

    def __init__(self, proposal_id: int, address: str, accepted: bool = None):
        self.proposal_id = proposal_id
        self.address = address[:255]
        self.accepted = accepted
        self.date_created = datetime.datetime.now()

    @staticmethod
    def get_pending_for_user(user):
        return ProposalTeamInvite.query.filter(
            ProposalTeamInvite.accepted == None,
            (func.lower(user.email_address) == func.lower(ProposalTeamInvite.address))
        ).all()


class ProposalUpdate(db.Model):
    __tablename__ = "proposal_update"

    id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.DateTime)

    proposal_id = db.Column(db.Integer, db.ForeignKey("proposal.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __init__(self, proposal_id: int, title: str, content: str):
        self.id = gen_random_id(ProposalUpdate)
        self.proposal_id = proposal_id
        self.title = title[:255]
        self.content = content
        self.date_created = datetime.datetime.now()


class ProposalArbiter(db.Model):
    __tablename__ = "proposal_arbiter"

    id = db.Column(db.Integer(), primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposal.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    status = db.Column(db.String(255), nullable=False)

    proposal = db.relationship("Proposal", lazy=True, back_populates="arbiter")
    user = db.relationship("User", uselist=False, lazy=True, back_populates="arbiter_proposals")

    def __init__(self, proposal_id: int, user_id: int = None, status: str = ProposalArbiterStatus.MISSING):
        self.id = gen_random_id(ProposalArbiter)
        self.proposal_id = proposal_id
        self.user_id = user_id
        self.status = status

    def accept_nomination(self, user_id: int):
        if self.user_id == user_id:
            self.status = ProposalArbiterStatus.ACCEPTED
            db.session.add(self)
            db.session.commit()
            return
        raise ValidationException('User not nominated for arbiter')

    def reject_nomination(self, user_id: int):
        if self.user_id == user_id:
            self.status = ProposalArbiterStatus.MISSING
            self.user = None
            db.session.add(self)
            db.session.commit()
            return
        raise ValidationException('User is not arbiter')


class Proposal(db.Model):
    __tablename__ = "proposal"

    id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.DateTime)
    rfp_id = db.Column(db.Integer(), db.ForeignKey('rfp.id'), nullable=True)

    # Content info
    status = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    brief = db.Column(db.String(255), nullable=False)
    stage = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(255), nullable=False)
    date_approved = db.Column(db.DateTime)
    date_published = db.Column(db.DateTime)
    reject_reason = db.Column(db.String())

    # Payment info
    target = db.Column(db.String(255), nullable=False)
    payout_address = db.Column(db.String(255), nullable=False)
    rfp_opt_in = db.Column(db.Boolean(), nullable=True)

    # Relations
    team = db.relationship("User", secondary=proposal_team)
    comments = db.relationship(Comment, backref="proposal", lazy=True, cascade="all, delete-orphan")
    updates = db.relationship(ProposalUpdate, backref="proposal", lazy=True, cascade="all, delete-orphan")
    milestones = db.relationship("Milestone", backref="proposal",
                                 order_by="asc(Milestone.index)", lazy=True, cascade="all, delete-orphan")
    invites = db.relationship(ProposalTeamInvite, backref="proposal", lazy=True, cascade="all, delete-orphan")
    arbiter = db.relationship(ProposalArbiter, uselist=False, back_populates="proposal", cascade="all, delete-orphan")

    def __init__(
            self,
            status: str = ProposalStatus.DRAFT,
            title: str = '',
            brief: str = '',
            content: str = '',
            stage: str = ProposalStage.PREVIEW,
            target: str = '0',
            payout_address: str = '',
            category: str = ''
    ):
        self.id = gen_random_id(Proposal)
        self.date_created = datetime.datetime.now()
        self.status = status
        self.title = title
        self.brief = brief
        self.content = content
        self.category = category
        self.target = target
        self.payout_address = payout_address
        self.stage = stage

    @staticmethod
    def simple_validate(proposal):
        # Validate fields to be database save-able.
        # Stricter validation is done in validate_publishable.
        stage = proposal.get('stage')
        category = proposal.get('category')

        if stage and not ProposalStage.includes(stage):
            raise ValidationException("Proposal stage {} is not a valid stage".format(stage))
        if category and not Category.includes(category):
            raise ValidationException("Category {} not a valid category".format(category))

    def validate_publishable_milestones(self):
        payout_total = 0.0
        for i, milestone in enumerate(self.milestones):

            if milestone.immediate_payout and i != 0:
                raise ValidationException("Only the first milestone can have an immediate payout")

            if len(milestone.title) > 60:
                raise ValidationException("Milestone title cannot be longer than 60 chars")

            if len(milestone.content) > 200:
                raise ValidationException("Milestone content cannot be longer than 200 chars")

            try:
                p = float(milestone.payout_percent)
                if not p.is_integer():
                    raise ValidationException("Milestone payout percents must be whole numbers, no decimals")
                if p <= 0 or p > 100:
                    raise ValidationException("Milestone payout percent must be greater than zero")
            except ValueError:
                raise ValidationException("Milestone payout percent must be a number")

            payout_total += p

        if payout_total != 100.0:
            raise ValidationException("Payout percentages of milestones must add up to exactly 100%")

    def validate_publishable(self):
        self.validate_publishable_milestones()

        # Require certain fields
        required_fields = ['title', 'content', 'brief', 'category', 'target', 'payout_address']
        for field in required_fields:
            if not hasattr(self, field):
                raise ValidationException("Proposal must have a {}".format(field))

        # Stricter limits on certain fields
        if len(self.title) > 60:
            raise ValidationException("Proposal title cannot be longer than 60 characters")
        if len(self.brief) > 140:
            raise ValidationException("Brief cannot be longer than 140 characters")
        if len(self.content) > 250000:
            raise ValidationException("Content cannot be longer than 250,000 characters")

        # Check with node that the address is kosher
        try:
            res = blockchain_get('/validate/address', {'address': self.payout_address})
        except:
            raise ValidationException(
                "Could not validate your payout address due to an internal server error, please try again later")
        if not res['valid']:
            raise ValidationException("Payout address is not a valid Zcash address")

        # Then run through regular validation
        Proposal.simple_validate(vars(self))

    # only do this when user submits for approval, there is a chance the dates will
    # be passed by the time admin approval / user publishing occurs
    def validate_milestone_dates(self):
        present = datetime.datetime.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        for milestone in self.milestones:
            if present > milestone.date_estimated:
                raise ValidationException("Milestone date estimate must be in the future ")

    @staticmethod
    def create(**kwargs):
        Proposal.simple_validate(kwargs)
        proposal = Proposal(
            **kwargs
        )

        # arbiter needs proposal.id
        db.session.add(proposal)
        db.session.flush()

        arbiter = ProposalArbiter(proposal_id=proposal.id)
        db.session.add(arbiter)

        return proposal

    @staticmethod
    def get_by_user(user, statuses=[ProposalStatus.LIVE]):
        status_filter = or_(Proposal.status == v for v in statuses)
        return Proposal.query \
            .join(proposal_team) \
            .filter(proposal_team.c.user_id == user.id) \
            .filter(status_filter) \
            .all()

    def update(
            self,
            title: str = '',
            brief: str = '',
            category: str = '',
            content: str = '',
            target: str = '0',
            payout_address: str = '',
    ):
        self.title = title[:255]
        self.brief = brief[:255]
        self.category = category
        self.content = content[:300000]
        self.target = target[:255] if target != '' else '0'
        self.payout_address = payout_address[:255]
        Proposal.simple_validate(vars(self))


    def send_admin_email(self, type: str):
        from grant.user.models import User
        admins = User.get_admins()
        for a in admins:
            send_email(a.email_address, type, {
                'user': a,
                'proposal': self,
                'proposal_url': make_admin_url(f'/proposals/{self.id}'),
            })

    # state: status (DRAFT || REJECTED) -> (PENDING || STAKING)
    def submit_for_approval(self):
        self.validate_publishable()
        self.validate_milestone_dates()
        allowed_statuses = [ProposalStatus.DRAFT, ProposalStatus.REJECTED]
        # specific validation
        if self.status not in allowed_statuses:
            raise ValidationException(f"Proposal status must be draft or rejected to submit for approval")

        self.send_admin_email('admin_approval')
        self.status = ProposalStatus.PENDING
        db.session.add(self)
        db.session.flush()

    # state: status PENDING -> (APPROVED || REJECTED)
    def approve_pending(self, is_approve, reject_reason=None):
        self.validate_publishable()
        # specific validation
        if not self.status == ProposalStatus.PENDING:
            raise ValidationException(f"Proposal must be pending to approve or reject")

        if is_approve:
            self.status = ProposalStatus.APPROVED
            self.date_approved = datetime.datetime.now()
            for t in self.team:
                send_email(t.email_address, 'proposal_approved', {
                    'user': t,
                    'proposal': self,
                    'proposal_url': make_url(f'/proposals/{self.id}'),
                    'admin_note': 'Congratulations! Your proposal has been approved.'
                })
        else:
            if not reject_reason:
                raise ValidationException("Please provide a reason for rejecting the proposal")
            self.status = ProposalStatus.REJECTED
            self.reject_reason = reject_reason
            for t in self.team:
                send_email(t.email_address, 'proposal_rejected', {
                    'user': t,
                    'proposal': self,
                    'proposal_url': make_url(f'/proposals/{self.id}'),
                    'admin_note': reject_reason
                })

    # state: status APPROVE -> LIVE, stage PREVIEW -> FUNDING_REQUIRED
    def publish(self):
        self.validate_publishable()
        # specific validation
        if not self.status == ProposalStatus.APPROVED:
            raise ValidationException(f"Proposal status must be approved")
        self.date_published = datetime.datetime.now()
        self.status = ProposalStatus.LIVE
        self.stage = ProposalStage.FUNDING_REQUIRED

    def cancel(self):
        if self.status != ProposalStatus.LIVE:
            raise ValidationException("Cannot cancel a proposal until it's live")

        self.stage = ProposalStage.CANCELED
        db.session.add(self)
        db.session.flush()

        # Send emails to team & contributors
        for u in self.team:
            send_email(u.email_address, 'proposal_canceled', {
                'proposal': self,
                'support_url': make_url('/contact'),
            })

    @hybrid_property
    def is_failed(self):
        if not self.status == ProposalStatus.LIVE or not self.date_published:
            return False
        if self.stage == ProposalStage.FAILED or self.stage == ProposalStage.CANCELED:
            return True
        return False

    @hybrid_property
    def current_milestone(self):
        if self.milestones:
            for ms in self.milestones:
                if ms.stage != MilestoneStage.PAID:
                    return ms
            return self.milestones[-1]  # return last one if all PAID
        return None


class ProposalSchema(ma.Schema):
    class Meta:
        model = Proposal
        # Fields to expose
        fields = (
            "stage",
            "status",
            "date_created",
            "date_approved",
            "date_published",
            "reject_reason",
            "title",
            "brief",
            "proposal_id",
            "target",
            "is_failed",
            "content",
            "updates",
            "milestones",
            "current_milestone",
            "category",
            "team",
            "payout_address",
            "invites",
            "rfp",
            "rfp_opt_in",
            "arbiter"
        )

    date_created = ma.Method("get_date_created")
    date_approved = ma.Method("get_date_approved")
    date_published = ma.Method("get_date_published")
    proposal_id = ma.Method("get_proposal_id")

    updates = ma.Nested("ProposalUpdateSchema", many=True)
    team = ma.Nested("UserSchema", many=True)
    milestones = ma.Nested("MilestoneSchema", many=True)
    current_milestone = ma.Nested("MilestoneSchema")
    invites = ma.Nested("ProposalTeamInviteSchema", many=True)
    rfp = ma.Nested("RFPSchema", exclude=["accepted_proposals"])
    arbiter = ma.Nested("ProposalArbiterSchema", exclude=["proposal"])

    def get_proposal_id(self, obj):
        return obj.id

    def get_date_created(self, obj):
        return dt_to_unix(obj.date_created)

    def get_date_approved(self, obj):
        return dt_to_unix(obj.date_approved) if obj.date_approved else None

    def get_date_published(self, obj):
        return dt_to_unix(obj.date_published) if obj.date_published else None


proposal_schema = ProposalSchema()
proposals_schema = ProposalSchema(many=True)
user_fields = [
    "proposal_id",
    "status",
    "title",
    "brief",
    "target",
    "date_created",
    "date_approved",
    "date_published",
    "reject_reason",
    "team",
]
user_proposal_schema = ProposalSchema(only=user_fields)
user_proposals_schema = ProposalSchema(many=True, only=user_fields)


class ProposalUpdateSchema(ma.Schema):
    class Meta:
        model = ProposalUpdate
        # Fields to expose
        fields = (
            "update_id",
            "date_created",
            "proposal_id",
            "title",
            "content"
        )

    date_created = ma.Method("get_date_created")
    proposal_id = ma.Method("get_proposal_id")
    update_id = ma.Method("get_update_id")

    def get_update_id(self, obj):
        return obj.id

    def get_proposal_id(self, obj):
        return obj.proposal_id

    def get_date_created(self, obj):
        return dt_to_unix(obj.date_created)


proposal_update_schema = ProposalUpdateSchema()
proposals_update_schema = ProposalUpdateSchema(many=True)


class ProposalTeamInviteSchema(ma.Schema):
    class Meta:
        model = ProposalTeamInvite
        fields = (
            "id",
            "date_created",
            "address",
            "accepted"
        )

    date_created = ma.Method("get_date_created")

    def get_date_created(self, obj):
        return dt_to_unix(obj.date_created)


proposal_team_invite_schema = ProposalTeamInviteSchema()
proposal_team_invites_schema = ProposalTeamInviteSchema(many=True)


class InviteWithProposalSchema(ma.Schema):
    class Meta:
        model = ProposalTeamInvite
        fields = (
            "id",
            "date_created",
            "address",
            "accepted",
            "proposal"
        )

    date_created = ma.Method("get_date_created")
    proposal = ma.Nested("ProposalSchema")

    def get_date_created(self, obj):
        return dt_to_unix(obj.date_created)


invite_with_proposal_schema = InviteWithProposalSchema()
invites_with_proposal_schema = InviteWithProposalSchema(many=True)




class ProposalArbiterSchema(ma.Schema):
    class Meta:
        model = ProposalArbiter
        fields = (
            "id",
            "user",
            "proposal",
            "status"
        )

    user = ma.Nested("UserSchema")  # , exclude=['arbiter_proposals'] (if UserSchema ever includes it)
    proposal = ma.Nested("ProposalSchema", exclude=['arbiter'])


user_proposal_arbiter_schema = ProposalArbiterSchema(exclude=['user'])
user_proposal_arbiters_schema = ProposalArbiterSchema(many=True, exclude=['user'])
