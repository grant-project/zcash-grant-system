import React from 'react';
import { connect } from 'react-redux';
import { Icon, Button, Input, message } from 'antd';
import { AppState } from 'store/reducers';
import { proposalActions } from 'modules/proposals';
import { rfpActions } from 'modules/rfps';
import { ProposalDetail } from 'modules/proposals/reducers';
import { Comment, RFP } from 'types';
import { likeProposal, likeComment, likeRfp } from 'api/api';
import AuthButton from 'components/AuthButton';
import './index.less';

interface OwnProps {
  proposal?: ProposalDetail | null;
  comment?: Comment;
  rfp?: RFP;
}

interface StateProps {
  authUser: AppState['auth']['user'];
}

interface DispatchProps {
  fetchProposal: typeof proposalActions['fetchProposal'];
  updateComment: typeof proposalActions['updateProposalComment'];
  fetchRfp: typeof rfpActions['fetchRfp'];
}

type Props = OwnProps & StateProps & DispatchProps;

const STATE = {
  loading: false,
};
type State = typeof STATE;

class Follow extends React.Component<Props, State> {
  state: State = { ...STATE };

  render() {
    const { likesCount, authedLiked, mode } = this.deriveInfo();
    const { loading } = this.state;
    const zoom = mode === 'comment' ? 0.8 : 1;
    return (
      <Input.Group className="Like" compact style={{ zoom }}>
        <AuthButton onClick={this.handleLike}>
          <Icon
            theme={authedLiked ? 'filled' : 'outlined'}
            type={loading ? 'loading' : 'like'}
          />
          {mode !== 'comment' && (
            <span className="Like-label">{authedLiked ? ' Unlike' : ' Like'}</span>
          )}
        </AuthButton>
        <Button className="Like-count" disabled>
          <span>{likesCount}</span>
        </Button>
      </Input.Group>
    );
  }

  private deriveInfo = () => {
    let authedLiked = false;
    let likesCount = 0;
    let mode: 'comment' | 'proposal' | 'rfp' | null = null;

    const { proposal, comment, rfp } = this.props;

    if (comment) {
      authedLiked = comment.authedLiked;
      likesCount = comment.likesCount;
      mode = 'comment';
    } else if (proposal) {
      authedLiked = proposal.authedLiked;
      likesCount = proposal.likesCount;
      mode = 'proposal';
    } else if (rfp) {
      authedLiked = rfp.authedLiked;
      likesCount = rfp.likesCount;
      mode = 'rfp';
    }

    return {
      authedLiked,
      likesCount,
      mode,
    };
  };

  private handleLike = () => {
    if (this.state.loading) return;

    const { mode } = this.deriveInfo();

    if (mode === 'proposal') {
      return this.handleProposalLike();
    }
    if (mode === 'comment') {
      return this.handleCommentLike();
    }
    if (mode === 'rfp') {
      return this.handleRfpLike();
    }
  };

  private handleProposalLike = async () => {
    if (!this.props.proposal) return;

    const { proposalId, authedLiked } = this.props.proposal;
    this.setState({ loading: true });
    try {
      await likeProposal(proposalId, !authedLiked);
      await this.props.fetchProposal(proposalId);
      message.success(<>Proposal {authedLiked ? 'unliked' : 'liked'}</>);
    } catch (error) {
      // tslint:disable:no-console
      console.error('Like.handleProposalLike - unable to change like state', error);
      message.error('Unable to like proposal');
    }
    this.setState({ loading: false });
  };

  private handleCommentLike = async () => {
    if (!this.props.comment) return;

    // const { proposalId } = this.props.proposal;
    const { id, authedLiked } = this.props.comment;
    this.setState({ loading: true });
    try {
      const updatedComment = await likeComment(id, !authedLiked);
      this.props.updateComment(this.props.comment.id, updatedComment);
      message.success(<>Comment {authedLiked ? 'unliked' : 'liked'}</>);
    } catch (error) {
      // tslint:disable:no-console
      console.error('Like.handleCommentLike - unable to change like state', error);
      message.error('Unable to like comment');
    }
    this.setState({ loading: false });
  };

  private handleRfpLike = async () => {
    if (!this.props.rfp) return;

    const { id, authedLiked } = this.props.rfp;
    this.setState({ loading: true });
    try {
      await likeRfp(id, !authedLiked);
      await this.props.fetchRfp(id);
      message.success(<>Request for proposal {authedLiked ? 'unliked' : 'liked'}</>);
    } catch (error) {
      // tslint:disable:no-console
      console.error('Like.handleRfpLike - unable to change like state', error);
      message.error('Unable to like rfp');
    }
    this.setState({ loading: false });
  };
}

const withConnect = connect<StateProps, DispatchProps, OwnProps, AppState>(
  state => ({
    authUser: state.auth.user,
  }),
  {
    fetchProposal: proposalActions.fetchProposal,
    updateComment: proposalActions.updateProposalComment,
    fetchRfp: rfpActions.fetchRfp,
  },
);

export default withConnect(Follow);
