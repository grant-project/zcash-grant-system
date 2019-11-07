import React from 'react';
import { connect } from 'react-redux';
import { Link } from 'react-router-dom';
import { Button, Tooltip } from 'antd';
import { SocialMedia } from 'types';
import { UserState } from 'modules/users/reducers';
import UserAvatar from 'components/UserAvatar';
import TipJarModal from 'components/TipJarModal';
import { SOCIAL_INFO } from 'utils/social';
import { AppState } from 'store/reducers';
import './ProfileUser.less';

interface OwnProps {
  user: UserState;
}

interface StateProps {
  authUser: AppState['auth']['user'];
}

type Props = OwnProps & StateProps;

const STATE = {
  tipJarModalOpen: false,
};

type State = typeof STATE;

class ProfileUser extends React.Component<Props, State> {
  state = STATE;

  render() {
    const {
      authUser,
      user,
      user: { socialMedias },
    } = this.props;

    const { tipJarModalOpen } = this.state;

    const isSelf = !!authUser && authUser.userid === user.userid;
    const tipJarDisabled = !user.tipJarAddress;
    const tipJarTooltip = tipJarDisabled ? 'User has not set a tip jar address' : '';

    return (
      <div className="ProfileUser">
        <div className="ProfileUser-avatar">
          <UserAvatar className="ProfileUser-avatar-img" user={user} />
        </div>
        <div className="ProfileUser-info">
          <div className="ProfileUser-info-name">{user.displayName}</div>
          <div className="ProfileUser-info-title">{user.title}</div>
          {socialMedias.length > 0 && (
            <div className="ProfileUser-info-social">
              {socialMedias.map(sm => (
                <Social key={sm.service} socialMedia={sm} />
              ))}
            </div>
          )}
          {isSelf && (
            <div>
              <Link to={`/profile/${user.userid}/edit`}>
                <Button>Edit profile</Button>
              </Link>
            </div>
          )}
          {!isSelf && (
            <div>
              <Tooltip placement={'bottomLeft'} title={tipJarTooltip}>
                <Button onClick={this.handleTipJarModalOpen} disabled={tipJarDisabled}>
                  Send tip
                </Button>
              </Tooltip>
            </div>
          )}
        </div>

        {!!user.tipJarAddress && (
          <TipJarModal
            isOpen={tipJarModalOpen}
            onClose={this.handleTipJarModalClose}
            type={'user'}
            address={user.tipJarAddress}
          />
        )}
      </div>
    );
  }

  private handleTipJarModalOpen = () =>
    this.setState({
      tipJarModalOpen: true,
    });

  private handleTipJarModalClose = () =>
    this.setState({
      tipJarModalOpen: false,
    });
}

const Social = ({ socialMedia }: { socialMedia: SocialMedia }) => {
  return (
    <a href={socialMedia.url} target="_blank" rel="noopener nofollow">
      <div className="ProfileUser-info-social-icon">
        {SOCIAL_INFO[socialMedia.service].icon}
      </div>
    </a>
  );
};

const connectedProfileUser = connect<StateProps, {}, {}, AppState>(state => ({
  authUser: state.auth.user,
}))(ProfileUser);

export default connectedProfileUser;
