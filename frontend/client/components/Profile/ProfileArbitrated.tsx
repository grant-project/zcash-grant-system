import React from 'react';
import { Link } from 'react-router-dom';
import moment from 'moment';
import { UserProposalArbiter, PROPOSAL_ARBITER_STATUS, MILESTONE_STAGE } from 'types';
import { connect } from 'react-redux';
import { AppState } from 'store/reducers';
import { updateUserArbiter } from 'api/api';
import { usersActions } from 'modules/users';
import { Button, Popconfirm, message } from 'antd';
import './ProfileArbitrated.less';

const PAS = PROPOSAL_ARBITER_STATUS;

interface OwnProps {
  arbiter: UserProposalArbiter;
}

interface StateProps {
  user: AppState['auth']['user'];
}

interface DispatchProps {
  fetchUser: typeof usersActions['fetchUser'];
}

type Props = OwnProps & StateProps & DispatchProps;

class ProfileArbitrated extends React.Component<Props, {}> {
  render() {
    const { status } = this.props.arbiter;
    const { title, proposalId, currentMilestone } = this.props.arbiter.proposal;
    const isMsPayoutReq =
      currentMilestone && currentMilestone.stage === MILESTONE_STAGE.REQUESTED;
    const msTitle = currentMilestone && currentMilestone.title;

    const info = {
      [PAS.MISSING]: <>{/* nada */}</>,
      [PAS.NOMINATED]: <>You have been nominated to be the arbiter for this proposal.</>,
      [PAS.ACCEPTED]: (
        <>
          {isMsPayoutReq && (
            <>
              The team has requested payout for <b>{msTitle}</b>{' '}
              {moment((currentMilestone!.dateRequested || 0) * 1000).fromNow()}. Please
              click the button to proceed.
            </>
          )}
          {!isMsPayoutReq && (
            <>
              As arbiter of this proposal, you are responsible for reviewing milestone
              payout requests.{' '}
            </>
          )}
          <br />
          <br />
          You may{' '}
          <Popconfirm
            title="Stop acting as arbiter?"
            onConfirm={() => this.acceptArbiter(false)}
          >
            <a href="#">opt out</a>
          </Popconfirm>{' '}
          at any time.
        </>
      ),
    };

    const actions = {
      [PAS.MISSING]: <>{/* nada */}</>,
      [PAS.NOMINATED]: (
        <>
          <Button onClick={() => this.acceptArbiter(true)} type="primary">
            Accept
          </Button>
          <Button onClick={() => this.acceptArbiter(false)}>Reject</Button>
        </>
      ),
      [PAS.ACCEPTED]: (
        <>
          {isMsPayoutReq && (
            <Link to={`/proposals/${proposalId}?tab=milestones`}>
              <Button type="primary">Review Milestone</Button>
            </Link>
          )}
        </>
      ),
    };

    return (
      <div className="ProfileArbitrated">
        <div className="ProfileArbitrated-block">
          <Link to={`/proposals/${proposalId}`} className="ProfileArbitrated-title">
            {title}
          </Link>
          <div className={`ProfileArbitrated-info`}>{info[status]}</div>
        </div>
        <div className="ProfileArbitrated-block is-actions">{actions[status]}</div>
      </div>
    );
  }

  private acceptArbiter = async (isAccept: boolean) => {
    const {
      arbiter: { proposal },
      user,
      fetchUser,
    } = this.props;
    await updateUserArbiter(user!.userid, proposal.proposalId, isAccept);
    message.success(isAccept ? 'Accepted arbiter position' : 'Rejected arbiter position');
    // refetch all the user data (includes the arbiter proposals)
    await fetchUser(String(user!.userid));
  };
}

export default connect<StateProps, DispatchProps, OwnProps, AppState>(
  state => ({
    user: state.auth.user,
  }),
  { fetchUser: usersActions.fetchUser },
)(ProfileArbitrated);
