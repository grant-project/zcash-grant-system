from grant.utils.requests import blockchain_post
from grant.proposal.models import (
    ProposalContribution,
    proposal_contributions_schema,
    PENDING,
    CONFIRMED,
  )

def make_bootstrap_data():
  pending_contributions = ProposalContribution.query \
    .filter_by(status=PENDING) \
    .all()
  latest_contribution = ProposalContribution.query\
    .filter_by(status=CONFIRMED) \
    .order_by(ProposalContribution.date_created.desc()) \
    .first()
  return {
    "pendingContributions": proposal_contributions_schema.dump(pending_contributions),
    "latestTxId": latest_contribution.tx_id if latest_contribution else None,
  }

def send_bootstrap_data():
  data = make_bootstrap_data()
  print('Sending bootstrap data to blockchain watcher microservice')
  print(' * Latest transaction ID: {}'.format(data['latestTxId']))
  print(' * Number of pending contributions: {}'.format(len(data['pendingContributions'])))

  res = blockchain_post('/bootstrap', data)
  print('Blockchain watcher has started')
  print('Starting chain height: {}'.format(res['startHeight']))
  print('Current chain height: {}'.format(res['currentHeight']))
