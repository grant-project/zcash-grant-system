import React from 'react';
import { Link } from 'react-router-dom';
import { Tag, Tooltip } from 'antd';
import UnitDisplay from 'components/UnitDisplay';
import { formatTxExplorerUrl } from 'utils/formatters';
import { UserContribution } from 'types';
import './ProfileContribution.less';

interface OwnProps {
  userId: number;
  contribution: UserContribution;
}

type Props = OwnProps;

class ProfileContribution extends React.Component<Props> {
  render() {
    const { contribution } = this.props;
    const { proposal, private: isPrivate } = contribution;
    const isConfirmed = contribution.status === 'CONFIRMED';

    let actions: React.ReactNode;
    if (isConfirmed) {
      actions = (
        <a
          href={formatTxExplorerUrl(contribution.txId as string)}
          target="_blank"
          rel="noopener nofollow"
        >
          View transaction
        </a>
      );
    }

    const privateTag = isPrivate ? (
      <Tooltip
        title={
          <>
            Other users will <b>not</b> be able to see that you made this contribution.
          </>
        }
      >
        <Tag>Private</Tag>
      </Tooltip>
    ) : null;

    return (
      <div className="ProfileContribution">
        <div className="ProfileContribution-info">
          <Link
            className="ProfileContribution-info-title"
            to={`/proposals/${proposal.proposalId}`}
          >
            {proposal.title} {privateTag}
          </Link>
          <div className="ProfileContribution-info-brief">{proposal.brief}</div>
        </div>
        <div className="ProfileContribution-state">
          <div className="ProfileContribution-state-amount">
            +<UnitDisplay value={contribution.amount} symbol="ZEC" unit="zat" />
          </div>
          <div className="ProfileContribution-state-actions">{actions}</div>
        </div>
      </div>
    );
  }
}

export default ProfileContribution;
