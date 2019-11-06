import json
from datetime import datetime, timedelta

from grant.task.models import Task, db
from grant.utils.enums import ProposalStatus
from grant.utils import totp_2fa
from grant.task.jobs import MilestoneDeadline

from ..config import BaseProposalCreatorConfig
from ..test_data import mock_blockchain_api_requests

from mock import patch, Mock

test_update = {
    "title": "Update Title",
    "content": "Update content."
}


class TestTaskAPI(BaseProposalCreatorConfig):
    def p(self, path, data):
        return self.app.post(path, data=json.dumps(data), content_type="application/json")

    def login_admin(self):
        # set admin
        self.user.set_admin(True)
        db.session.commit()

        # login
        r = self.p("/api/v1/admin/login", {
            "username": self.user.email_address,
            "password": self.user_password
        })
        self.assert200(r)

        # 2fa on the natch
        r = self.app.get("/api/v1/admin/2fa")
        self.assert200(r)

        # ... init
        r = self.app.get("/api/v1/admin/2fa/init")
        self.assert200(r)

        codes = r.json['backupCodes']
        secret = r.json['totpSecret']
        uri = r.json['totpUri']

        # ... enable/verify
        r = self.p("/api/v1/admin/2fa/enable", {
            "backupCodes": codes,
            "totpSecret": secret,
            "verifyCode": totp_2fa.current_totp(secret)
        })
        self.assert200(r)
        return r

    def test_proposal_reminder_task_is_created(self):
        tasks = Task.query.filter(Task.execute_after <= datetime.now()).filter_by(completed=False).all()
        self.assertEqual(tasks, [])
        self.make_proposal_reminder_task()
        tasks = Task.query.filter(Task.execute_after <= datetime.now()).filter_by(completed=False).all()
        self.assertEqual(len(tasks), 1)

    def test_proposal_reminder_task_is_marked_completed_after_call(self):
        self.make_proposal_reminder_task()
        tasks = Task.query.filter(Task.execute_after <= datetime.now()).filter_by(completed=False).all()
        self.assertEqual(len(tasks), 1)
        self.app.get("/api/v1/task")
        tasks = Task.query.filter(Task.execute_after <= datetime.now()).filter_by(completed=False).all()
        self.assertEqual(tasks, [])

