import React from 'react';
import { Redirect } from 'react-router-dom';
import classnames from 'classnames';
import { Progress, Tag } from 'antd';
import { Proposal, STATUS } from 'types';
import Card from 'components/Card';
import UserAvatar from 'components/UserAvatar';
import UnitDisplay from 'components/UnitDisplay';
import { formatUsd } from 'utils/formatters';
import './style.less';

interface OwnProps {
  minCardHeight: number;
  setMinCardHeight: (height: number) => void;
}

type Props = OwnProps & Proposal;

export class ProposalCard extends React.Component<Props> {
  innerDiv: HTMLDivElement | null = null;

  state = { redirect: '' };

  updateCardHeight = () => {
    if (this.innerDiv && this.props.isVersionTwo) {
      const { height } = this.innerDiv.getBoundingClientRect();
      this.props.setMinCardHeight(height);
    }
  };

  componentDidMount() {
    if (this.props.isVersionTwo) {
      window.addEventListener('resize', this.updateCardHeight);
      this.updateCardHeight();
    }
  }

  componentWillUnmount() {
    if (this.props.isVersionTwo) {
      window.removeEventListener('resize', this.updateCardHeight);
    }
  }

  render() {
    if (this.state.redirect) {
      return <Redirect push to={this.state.redirect} />;
    }
    const {
      title,
      proposalAddress,
      proposalUrlId,
      datePublished,
      dateCreated,
      team,
      target,
      contributionMatching,
      isVersionTwo,
      funded,
      percentFunded,
      acceptedWithFunding,
      status,
      minCardHeight,
    } = this.props;

    // pulled from `variables.less`
    const infoColor = '#1890ff';
    const secondaryColor = '#2D2A26';

    let tagColor = '';
    let tagMessage = '';

    if (isVersionTwo && status === STATUS.DISCUSSION) {
      tagColor = infoColor;
      tagMessage = 'Open for Public Review';
    }

    if (isVersionTwo && status === STATUS.LIVE) {
      if (acceptedWithFunding) {
        tagColor = secondaryColor;
        tagMessage = 'Funded by ZF';
      } else {
        tagColor = infoColor;
        tagMessage = 'Not Funded';
      }
    }

    let wrapperStyle = {};
    if (!isVersionTwo) {
      wrapperStyle = {
        minHeight: `${minCardHeight}px`,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      };
    }

    return (
      <Card className="ProposalCard" to={`/proposals/${proposalUrlId}`} title={title}>
        <div ref={e => (this.innerDiv = e)} style={wrapperStyle}>
          {contributionMatching > 0 && (
            <div className="ProposalCard-ribbon">
              <span>
                x2
                <small>matching</small>
              </span>
            </div>
          )}
          {isVersionTwo && (
            <div className="ProposalCard-funding">
              <div className="ProposalCard-funding-raised">
                {formatUsd(target.toString(10))}
              </div>
              <div
                className="ProposalCard-funding-tag"
                style={!tagMessage ? { opacity: 0 } : {}}
              >
                <Tag color={tagColor}>{tagMessage}</Tag>
              </div>
            </div>
          )}

          {!isVersionTwo && (
            <>
              <div className="ProposalCard-funding-v1">
                <div className="ProposalCard-funding-v1-raised">
                  <UnitDisplay value={funded} symbol="ZEC" /> <small>raised</small> of{' '}
                  <UnitDisplay value={target} symbol="ZEC" /> goal
                </div>
                <div
                  className={classnames({
                    ['ProposalCard-funding-percent']: true,
                    ['is-funded']: percentFunded >= 100,
                  })}
                >
                  {percentFunded}%
                </div>
              </div>
              <Progress
                percent={percentFunded}
                status={percentFunded >= 100 ? 'success' : 'active'}
                showInfo={false}
              />
            </>
          )}

          <div className="ProposalCard-team">
            <div className={`ProposalCard-team-name${isVersionTwo ? '' : '-v1'}`}>
              {team[0].displayName}{' '}
              {team.length > 1 && <small>+{team.length - 1} other</small>}
            </div>
            <div className="ProposalCard-team-avatars">
              {[...team].reverse().map((u, idx) => (
                <UserAvatar
                  key={idx}
                  className={`ProposalCard-team-avatars-avatar${
                    isVersionTwo ? '' : '-v1'
                  }`}
                  user={u}
                />
              ))}
            </div>
          </div>
          <div className="ProposalCard-address">{proposalAddress}</div>
          <Card.Info proposal={this.props} time={(datePublished || dateCreated) * 1000} />
        </div>
      </Card>
    );
  }
}

export default ProposalCard;
