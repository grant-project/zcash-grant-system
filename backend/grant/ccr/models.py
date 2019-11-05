from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.hybrid import hybrid_property

from grant.extensions import ma, db
from grant.utils.enums import CCRStatus
from grant.utils.misc import gen_random_id


class CCR(db.Model):
    __tablename__ = "ccr"

    id = db.Column(db.Integer(), primary_key=True)
    date_created = db.Column(db.DateTime)

    title = db.Column(db.String(255), nullable=True)
    brief = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(255), nullable=False)
    _bounty = db.Column("bounty", db.String(255), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    author = db.relationship("User", back_populates="ccrs")

    @staticmethod
    def create(**kwargs):
        ccr = CCR(
            **kwargs
        )

        # arbiter needs proposal.id
        db.session.add(ccr)
        db.session.flush()

        return ccr

    @hybrid_property
    def bounty(self):
        return self._bounty

    @bounty.setter
    def bounty(self, bounty: str):
        if bounty and Decimal(bounty) > 0:
            self._bounty = bounty
        else:
            self._bounty = None

    def __init__(
            self,
            user_id: int,
            title: str = '',
            brief: str = '',
            content: str = '',
            bounty: str = '0',
            status: str = CCRStatus.DRAFT,
    ):
        assert CCRStatus.includes(status)
        self.id = gen_random_id(CCR)
        self.date_created = datetime.now()
        self.title = title[:255]
        self.brief = brief[:255]
        self.content = content
        self.bounty = bounty
        self.status = status
        self.user_id = user_id

    def update(
            self,
            title: str = '',
            brief: str = '',
            content: str = '',
            bounty: str = '0',
    ):
        self.title = title[:255]
        self.brief = brief[:255]
        self.content = content[:300000]
        self._bounty = bounty[:255] if bounty != '' else '0'


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
            "bounty",
            "date_created",
        )

    author = ma.Nested("UserSchema")
    ccr_id = ma.Method("get_ccr_id")

    def get_ccr_id(self, obj):
        return obj.id


ccr_schema = CCRSchema()
ccrs_schema = CCRSchema(many=True)

# class AdminRFPSchema(ma.Schema):
#     class Meta:
#         model = RFP
#         # Fields to expose
#         fields = (
#             "id",
#             "title",
#             "brief",
#             "content",
#             "category",
#             "status",
#             "bounty",
#             "date_created",
#             "proposals",
#         )
#
#     status = ma.Method("get_status")
#     date_created = ma.Method("get_date_created")
#     proposals = ma.Nested("ProposalSchema", many=True, exclude=["rfp"])
#
#     def get_status(self, obj):
#         # Force it into closed state if date_closes is in the past
#         if obj.date_closes and obj.date_closes <= datetime.today():
#             return RFPStatus.CLOSED
#         return obj.status
#
#     def get_date_created(self, obj):
#         return dt_to_unix(obj.date_created)
#
#     def get_date_closes(self, obj):
#         return dt_to_unix(obj.date_closes) if obj.date_closes else None
#
#     def get_date_opened(self, obj):
#         return dt_to_unix(obj.date_opened) if obj.date_opened else None
#
#     def get_date_closed(self, obj):
#         return dt_to_unix(obj.date_closes) if obj.date_closes else None
#
#
# admin_rfp_schema = AdminRFPSchema()
# admin_rfps_schema = AdminRFPSchema(many=True)
