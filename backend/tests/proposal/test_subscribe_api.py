from grant.proposal.models import Proposal, db
from grant.utils.enums import ProposalStatus
from ..config import BaseUserConfig


class TestProposalSubscribeAPI(BaseUserConfig):
    def test_unauthorized_proposal_subscribe(self):
        # no login
        proposal = Proposal(status=ProposalStatus.LIVE)
        db.session.add(proposal)
        db.session.commit()

        res = self.app.post(
            f"/api/v1/proposals/{proposal.id}/subscribe",
            content_type='application/json'
        )
        self.assertStatus(res, 401)

    def test_unauthorized_proposal_unsubscribe(self):
        # no login
        proposal = Proposal(status=ProposalStatus.LIVE)
        db.session.add(proposal)
        db.session.commit()

        res = self.app.delete(
            f"/api/v1/proposals/{proposal.id}/subscribe",
            content_type='application/json'
        )
        self.assertStatus(res, 401)

    def test_invalid_proposal_id_subscribe(self):
        self.login_default_user()
        res = self.app.post(
            "/api/v1/proposals/12345/subscribe",
            content_type='application/json'
        )
        self.assertStatus(res, 404)

    def test_invalid_proposal_id_unsubscribe(self):
        self.login_default_user()
        res = self.app.delete(
            "/api/v1/proposals/12345/subscribe",
            content_type='application/json'
        )
        self.assertStatus(res, 404)

    def test_proposal_subscribe_and_unsubscribe(self):
        self.login_default_user()
        proposal = Proposal(status=ProposalStatus.LIVE)
        db.session.add(proposal)
        db.session.commit()

        # should not be subscribed to new proposal
        proposal_res = self.app.get(
            f"/api/v1/proposals/{proposal.id}",
        )
        self.assertStatus(proposal_res, 200)
        self.assertFalse(proposal_res.json["isSubscribed"])

        # should be able to subscribe to new proposal
        subscribe_res = self.app.post(
            f"/api/v1/proposals/{proposal.id}/subscribe",
            content_type='application/json'
        )
        self.assertStatus(subscribe_res, 200)
        self.assertTrue(subscribe_res.json["isSubscribed"])

        # should not be able to resubscribe to proposal
        subscribe_res = self.app.post(
            f"/api/v1/proposals/{proposal.id}/subscribe",
            content_type='application/json'
        )
        self.assertStatus(subscribe_res, 404)
        self.assertEqual(subscribe_res.json["message"], "User is already subscribed to this proposal")

        # should be able to unsubscribe to proposal
        subscribe_res = self.app.delete(
            f"/api/v1/proposals/{proposal.id}/subscribe",
            content_type='application/json'
        )
        self.assertStatus(subscribe_res, 200)
        self.assertFalse(subscribe_res.json["isSubscribed"])

        # should not be able to unsubscribe again to proposal
        subscribe_res = self.app.delete(
            f"/api/v1/proposals/{proposal.id}/subscribe",
            content_type='application/json'
        )
        self.assertStatus(subscribe_res, 404)
        self.assertEqual(subscribe_res.json["message"], "User is not subscribed to this proposal")


