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
    _target = db.Column("target", db.String(255), nullable=True)

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
        )

    author = ma.Nested("UserSchema")
    ccr_id = ma.Method("get_ccr_id")

    def get_ccr_id(self, obj):
        return obj.id


ccr_schema = CCRSchema()
ccrs_schema = CCRSchema(many=True)
