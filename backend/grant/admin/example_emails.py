# Fake objects must be classes. Should stub out model properties.
class FakeUser(object):
    id = 123
    email_address = 'example@example.com'
    display_name = 'Example User'
    title = 'Email Example Dude'


class FakeMilestone(object):
    id = 123
    index = 0
    title = 'Example Milestone'


class FakeProposal(object):
    id = 123
    title = 'Example proposal'
    brief = 'This is an example proposal'
    content = 'Example example example example'
    target = "100"
    current_milestone = FakeMilestone()


class FakeUpdate(object):
    id = 123
    title = 'Example update'
    content = 'Example example example example\n\nExample example example example'
    proposal_id = 123


user = FakeUser()
proposal = FakeProposal()
milestone = FakeMilestone()
update = FakeUpdate()

example_email_args = {
    'signup': {
        'display_name': user.display_name,
        'confirm_url': 'http://someconfirmurl.com',
    },
    'team_invite': {
        'inviter': user,
        'proposal': proposal,
        'invite_url': 'http://someinviteurl.com',
    },
    'recover': {
        'recover_url': 'http://somerecoveryurl.com',
    },
    'change_email': {
        'display_name': user.display_name,
        'confirm_url': 'http://someconfirmurl.com',
    },
    'change_email_old': {
        'display_name': user.display_name,
        'contact_url': 'http://somecontacturl.com',
    },
    'change_password': {
        'display_name': user.display_name,
        'recover_url': 'http://somerecoverurl.com',
        'contact_url': 'http://somecontacturl.com',
    },
    'proposal_approved': {
        'proposal': proposal,
        'proposal_url': 'http://someproposal.com',
        'admin_note': 'This proposal was the hottest stuff our team has seen yet. We look forward to throwing the fat stacks at you.',
    },
    'proposal_rejected': {
        'proposal': proposal,
        'proposal_url': 'http://someproposal.com',
        'admin_note': 'We think that you’ve asked for too much money for the project you’ve proposed, and for such an inexperienced team. Feel free to change your target amount, or elaborate on why you need so much money, and try applying again.',
    },
    'proposal_comment': {
        'author': user,
        'proposal': proposal,
        'comment_url': 'http://somecomment.com',
        'author_url': 'http://someuser.com',
    },
    'proposal_failed': {
        'proposal': proposal,
    },
    'proposal_canceled': {
        'proposal': proposal,
        'support_url': 'http://linktosupport.com',
    },
    'comment_reply': {
        'author': user,
        'proposal': proposal,
        'comment_url': 'http://somecomment.com',
        'author_url': 'http://someuser.com',
    },
    'proposal_arbiter': {
        'proposal': proposal,
        'proposal_url': 'http://zfnd.org/proposals/999',
        'accept_url': 'http://zfnd.org/email/arbiter?code=blah&proposalId=999',
    },
    'milestone_request': {
        'proposal': proposal,
        'proposal_milestones_url': 'http://zfnd.org/proposals/999-my-proposal?tab=milestones',
    },
    'milestone_reject': {
        'proposal': proposal,
        'admin_note': 'We noticed that the tests were failing for the features outlined in this milestone. Please address these issues.',
        'proposal_milestones_url': 'http://zfnd.org/proposals/999-my-proposal?tab=milestones',
    },
    'milestone_accept': {
        'proposal': proposal,
        'amount': '33',
        'proposal_milestones_url': 'http://zfnd.org/proposals/999-my-proposal?tab=milestones',
    },
    'milestone_paid': {
        'proposal': proposal,
        'milestone': milestone,
        'amount': '33',
        'tx_explorer_url': 'http://someblockexplorer.com/tx/271857129857192579125',
        'proposal_milestones_url': 'http://zfnd.org/proposals/999-my-proposal?tab=milestones',
    },
    'admin_approval': {
        'proposal': proposal,
        'proposal_url': 'https://grants-admin.zfnd.org/proposals/999',
    },
    'admin_arbiter': {
        'proposal': proposal,
        'proposal_url': 'https://grants-admin.zfnd.org/proposals/999',
    },
    'admin_payout': {
        'proposal': proposal,
        'proposal_url': 'https://grants-admin.zfnd.org/proposals/999',
    },
}
