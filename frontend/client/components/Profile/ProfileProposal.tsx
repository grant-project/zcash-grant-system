import React from 'react';
import { Link } from 'react-router-dom';
import { UserProposal } from 'types';
import './ProfileProposal.less';
import UserRow from 'components/UserRow';
import UnitDisplay from 'components/UnitDisplay';

interface OwnProps {
  proposal: UserProposal;
}

export default class Profile extends React.Component<OwnProps> {
  render() {
    const { title, brief, team, proposalId, target } = this.props.proposal;
    return (
      <div className="ProfileProposal">
        <div className="ProfileProposal-block">
          <Link to={`/proposals/${proposalId}`} className="ProfileProposal-title">
            {title}
          </Link>
          <div className="ProfileProposal-brief">{brief}</div>
          <div className="ProfileProposal-raised">
            <UnitDisplay value={target} symbol="ZEC" displayShortBalance={4} /> goal
          </div>
        </div>
        <div className="ProfileProposal-block">
          <h3>Team</h3>
          <div className="ProfileProposal-block-team">
            {team.map(user => (
              <UserRow key={user.userid} user={user} />
            ))}
          </div>
        </div>
      </div>
    );
  }
}
