from datetime import datetime, timedelta

from grant.task.models import Task, db
from grant.task.jobs import PruneDraft
from grant.proposal.models import Proposal
from grant.utils.enums import ProposalStatus

from mock import patch, Mock

from ..config import BaseProposalCreatorConfig


class TestTaskAPI(BaseProposalCreatorConfig):

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

    @patch('grant.task.views.datetime')
    def test_proposal_pruning(self, mock_datetime):
        self.login_default_user()
        resp = self.app.post(
            "/api/v1/proposals/drafts",
        )
        proposal_id = resp.json['proposalId']

        # make sure proposal was created
        proposal = Proposal.query.get(proposal_id)
        self.assertIsNotNone(proposal)

        # make sure the task was created
        self.assertStatus(resp, 201)
        tasks = Task.query.all()
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(resp.json['proposalId'], task.blob['proposal_id'])
        self.assertFalse(task.completed)

        # mock time so task will run when called
        after_time = datetime.now() + timedelta(seconds=PruneDraft.PRUNE_TIME + 100)
        mock_datetime.now = Mock(return_value=after_time)

        # run task
        resp = self.app.get("/api/v1/task")
        self.assert200(resp)

        # make sure task ran successfully
        tasks = Task.query.all()
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertTrue(task.completed)
        proposal = Proposal.query.get(proposal_id)
        self.assertIsNone(proposal)

    @patch('grant.task.views.datetime')
    def test_proposal_pruning_skip_status(self, mock_datetime):
        # make sure proposals that are not drafts are not deleted
        mock_datetime.now = Mock(return_value=datetime.now())
        self.login_default_user()
        resp = self.app.post(
            "/api/v1/proposals/drafts"
        )
        proposal_id = resp.json["proposalId"]
        proposal = Proposal.query.get(proposal_id)
        proposal.status = ProposalStatus.LIVE
        db.session.add(proposal)
        db.session.commit()
        after_time = datetime.now() + timedelta(seconds=PruneDraft.PRUNE_TIME + 100)
        mock_datetime.now = Mock(return_value=after_time)

        resp = self.app.get("/api/v1/task")
        self.assert200(resp)

        tasks = Task.query.all()
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertTrue(task.completed)
        proposal = Proposal.query.get(proposal_id)
        self.assertIsNotNone(proposal)

    @patch('grant.task.views.datetime')
    def test_proposal_pruning_skip_content(self, mock_datetime):
        # make sure proposals that have populated fields are not deleted
        mock_datetime.now = Mock(return_value=datetime.now())
        self.login_default_user()
        resp = self.app.post(
            "/api/v1/proposals/drafts"
        )
        proposal_id = resp.json["proposalId"]
        proposal = Proposal.query.get(proposal_id)
        proposal.content = "content"
        db.session.add(proposal)
        db.session.commit()
        after_time = datetime.now() + timedelta(seconds=PruneDraft.PRUNE_TIME + 100)
        mock_datetime.now = Mock(return_value=after_time)

        resp = self.app.get("/api/v1/task")
        self.assert200(resp)

        tasks = Task.query.all()
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertTrue(task.completed)
        proposal = Proposal.query.get(proposal_id)
        self.assertIsNotNone(proposal)

