import json
from datetime import datetime, timedelta

from grant.task.models import Task, db
from grant.utils.enums import ProposalStatus
from grant.utils import totp_2fa
from grant.task.jobs import MilestoneDeadline

from ..config import BaseProposalCreatorConfig

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

    @patch('grant.task.jobs.send_email')
    @patch('grant.task.views.datetime')
    def test_milestone_deadline(self, mock_datetime, mock_send_email):
        tasks = Task.query.filter_by(completed=False).all()
        self.assertEqual(len(tasks), 0)

        self.proposal.arbiter.user = self.user
        db.session.add(self.proposal)

        # unset immediate_payout so task will be added
        for milestone in self.proposal.milestones:
            if milestone.immediate_payout:
                milestone.immediate_payout = False
                db.session.add(milestone)

        db.session.commit()

        self.login_admin()

        # proposal needs to be PENDING
        self.proposal.status = ProposalStatus.PENDING

        # approve proposal with funding
        resp = self.app.put(
            "/api/v1/admin/proposals/{}/accept".format(self.proposal.id),
            data=json.dumps({"isAccepted": True, "withFunding": True})
        )
        self.assert200(resp)

        tasks = Task.query.filter_by(completed=False).all()
        self.assertEqual(len(tasks), 1)

        # fast forward the clock so task will run
        after_time = datetime.now() + timedelta(days=365)
        mock_datetime.now = Mock(return_value=after_time)

        # run task
        resp = self.app.get("/api/v1/task")
        self.assert200(resp)

        # make sure task ran
        tasks = Task.query.filter_by(completed=False).all()
        self.assertEqual(len(tasks), 0)
        mock_send_email.assert_called()

    @patch('grant.task.jobs.send_email')
    def test_milestone_deadline_update_posted(self, mock_send_email):
        tasks = Task.query.all()
        self.assertEqual(len(tasks), 0)

        # set date_estimated on milestone to be in the past
        milestone = self.proposal.milestones[0]
        milestone.date_estimated = datetime.now() - timedelta(hours=1)
        db.session.add(milestone)
        db.session.commit()

        # make task
        ms_deadline = MilestoneDeadline(self.proposal, milestone)
        ms_deadline.make_task()

        # check make task
        tasks = Task.query.all()
        self.assertEqual(len(tasks), 1)

        # login and post proposal update
        self.login_default_user()
        resp = self.app.post(
            "/api/v1/proposals/{}/updates".format(self.proposal.id),
            data=json.dumps(test_update),
            content_type='application/json'
        )
        self.assertStatus(resp, 201)

        # run task
        resp = self.app.get("/api/v1/task")
        self.assert200(resp)

        # make sure task ran and did NOT send out an email
        tasks = Task.query.filter_by(completed=False).all()
        self.assertEqual(len(tasks), 0)
        mock_send_email.assert_not_called()