import React from 'react';
import { connect } from 'react-redux';
import { Icon } from 'antd';
import { Link } from 'react-router-dom';
import Result from 'ant-design-pro/lib/Result';
import Loader from 'components/Loader';
import { ccrActions } from 'modules/ccr';
import { AppState } from 'store/reducers';
import { getCCRStakingContribution } from 'api/api';
import './CCRFinal.less';
import PaymentInfo from 'components/ContributionModal/PaymentInfo';
import { ContributionWithAddresses } from 'types';

interface OwnProps {
  goBack(): void;
}

interface StateProps {
  form: AppState['ccr']['form'];
  submittedCCR: AppState['ccr']['submittedCCR'];
  submitError: AppState['ccr']['submitError'];
}

interface DispatchProps {
  submitCCR: typeof ccrActions['submitCCR'];
}

type Props = OwnProps & StateProps & DispatchProps;

const STATE = {
  contribution: null as null | ContributionWithAddresses,
  contributionError: null as null | Error,
};

type State = typeof STATE;

class CCRFinal extends React.Component<Props, State> {
  state = STATE;
  componentDidMount() {
    this.submit();
  }

  componentDidUpdate(prev: Props) {
    const { submittedCCR } = this.props;
    if (!prev.submittedCCR && submittedCCR) {
      if (!submittedCCR.isStaked) {
        this.getStakingContribution();
      }
    }
  }

  render() {
    const { submittedCCR, submitError, goBack } = this.props;
    const { contribution, contributionError } = this.state;

    const ready = submittedCCR && (submittedCCR.isStaked || contribution);
    const staked = submittedCCR && submittedCCR.isStaked;

    let content;
    if (submitError) {
      content = (
        <div className="CCRFinal-message is-error">
          <Icon type="close-circle" />
          <div className="CCRFinal-message-text">
            <h3>
              <b>Something went wrong during creation</b>
            </h3>
            <h5>{submitError}</h5>
            <a onClick={goBack}>Click here</a> to go back to the form and try again.
          </div>
        </div>
      );
    } else if (ready) {
      content = (
        <>
          <div className="CCRFinal-message is-success">
            <Icon type="check-circle" />
            {staked && (
              <div className="CCRFinal-message-text">
                Your request has been staked and submitted! Check your{' '}
                <Link to={`/profile?tab=pending`}>profile's pending requests tab</Link> to
                check its status.
              </div>
            )}
            {!staked && (
              <div className="CCRFinal-message-text">
                Your request has been submitted! Please send the staking contribution of{' '}
                <b>{contribution && contribution.amount} ZEC</b> using the instructions
                below.
              </div>
            )}
          </div>
          {!staked && (
            <>
              <div className="CCRFinal-contribute">
                <PaymentInfo
                  text={
                    <>
                      <p>
                        If you cannot send the payment now, you may bring up these
                        instructions again by visiting your{' '}
                        <Link to={`/profile?tab=funded`}>profile's funded tab</Link>.
                      </p>
                      <p>
                        Once your payment has been sent and processed with 6
                        confirmations, you will receive an email. Visit your{' '}
                        <Link to={`/profile?tab=pending`}>
                          profile's pending requests tab
                        </Link>{' '}
                        at any time to check its status.
                      </p>
                    </>
                  }
                  contribution={contribution}
                />
              </div>
              <p className="CCRFinal-staked">
                I'm finished, take me to{' '}
                <Link to="/profile?tab=pending">my pending requests</Link>!
              </p>
            </>
          )}
        </>
      );
    } else if (contributionError) {
      content = (
        <Result
          type="error"
          title="Something went wrong"
          description={
            <>
              We were unable to get your staking contribution started. You can finish
              staking from <Link to="/profile?tab=pending">your profile</Link>, please try
              again from there soon.
            </>
          }
        />
      );
    } else {
      content = <Loader size="large" tip="Submitting your request..." />;
    }

    return <div className="CCRFinal">{content}</div>;
  }

  private submit = () => {
    if (this.props.form) {
      this.props.submitCCR(this.props.form);
    }
  };

  private getStakingContribution = async () => {
    const { submittedCCR } = this.props;
    if (submittedCCR) {
      try {
        const res = await getCCRStakingContribution(submittedCCR.ccrId);
        this.setState({ contribution: res.data });
      } catch (err) {
        this.setState({ contributionError: err });
      }
    }
  };
}

export default connect<StateProps, DispatchProps, OwnProps, AppState>(
  (state: AppState) => ({
    form: state.ccr.form,
    submittedCCR: state.ccr.submittedCCR,
    submitError: state.ccr.submitError,
  }),
  {
    submitCCR: ccrActions.submitCCR,
  },
)(CCRFinal);
