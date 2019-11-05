import React from 'react';
import { connect } from 'react-redux';
import { compose } from 'recompose';
import { Steps, Icon } from 'antd';
import qs from 'query-string';
import { withRouter, RouteComponentProps } from 'react-router';
import { History } from 'history';
import { debounce } from 'underscore';
import Basics from './Basics';
import Details from './Details';
import Review from './Review';
import Preview from './Preview';
import Final from './Final';
import CCRSubmitWarningModal from './CCRSubmitWarningModal';
import { ccrActions } from 'modules/ccr';
import { CCRDraft } from 'types';
import { getCCRErrors } from 'modules/ccr/utils';

import { AppState } from 'store/reducers';

import './index.less';

export enum CCR_STEP {
  BASICS = 'BASICS',
  DETAILS = 'DETAILS',
  REVIEW = 'REVIEW',
}

const STEP_ORDER = [CCR_STEP.BASICS, CCR_STEP.DETAILS, CCR_STEP.REVIEW];

interface StepInfo {
  short: string;
  title: React.ReactNode;
  subtitle: React.ReactNode;
  help: React.ReactNode;
  component: any;
}
const STEP_INFO: { [key in CCR_STEP]: StepInfo } = {
  [CCR_STEP.BASICS]: {
    short: 'Basics',
    title: 'Let’s start with the basics',
    subtitle: 'Don’t worry, you can come back and change things before publishing',
    help:
      'You don’t have to fill out everything at once right now, you can come back later.',
    component: Basics,
  },
  [CCR_STEP.DETAILS]: {
    short: 'Details',
    title: 'Dive into the details',
    subtitle: 'Here’s your chance to lay out the full proposal, in all its glory',
    help:
      'Make sure people know what you’re building, why you’re qualified, and where the money’s going',
    component: Details,
  },
  [CCR_STEP.REVIEW]: {
    short: 'Review',
    title: 'Review your proposal',
    subtitle: 'Feel free to edit any field that doesn’t look right',
    help: 'You’ll get a chance to preview your proposal next before you publish it',
    component: Review,
  },
};

interface StateProps {
  form: AppState['ccr']['form'];
  isSavingDraft: AppState['ccr']['isSavingDraft'];
  hasSavedDraft: AppState['ccr']['hasSavedDraft'];
  saveDraftError: AppState['ccr']['saveDraftError'];
}

interface DispatchProps {
  updateCCRForm: typeof ccrActions['updateCCRForm'];
}

type Props = StateProps & DispatchProps & RouteComponentProps<any>;

interface State {
  step: CCR_STEP;
  isPreviewing: boolean;
  isShowingSubmitWarning: boolean;
  isSubmitting: boolean;
  isExample: boolean;
}

class CCRFlow extends React.Component<Props, State> {
  private historyUnlisten: () => void;
  private debouncedUpdateForm: (form: Partial<CCRDraft>) => void;

  constructor(props: Props) {
    super(props);
    const searchValues = qs.parse(props.location.search);
    const queryStep = searchValues.step ? searchValues.step.toUpperCase() : null;
    const step =
      queryStep && CCR_STEP[queryStep]
        ? (CCR_STEP[queryStep] as CCR_STEP)
        : CCR_STEP.BASICS;
    this.state = {
      step,
      isPreviewing: false,
      isSubmitting: false,
      isExample: false,
      isShowingSubmitWarning: false,
    };
    this.debouncedUpdateForm = debounce(this.updateForm, 800);
    this.historyUnlisten = this.props.history.listen(this.handlePop);
  }

  componentWillUnmount() {
    if (this.historyUnlisten) {
      this.historyUnlisten();
    }
  }

  render() {
    const { isSavingDraft, saveDraftError } = this.props;
    const { step, isPreviewing, isSubmitting, isShowingSubmitWarning } = this.state;

    const info = STEP_INFO[step];
    const currentIndex = STEP_ORDER.indexOf(step);
    const isLastStep = STEP_ORDER.indexOf(step) === STEP_ORDER.length - 1;
    const StepComponent = info.component;

    let content;
    let showFooter = true;
    if (isSubmitting) {
      content = <Final goBack={this.cancelSubmit} />;
      showFooter = false;
    } else if (isPreviewing) {
      content = <Preview />;
    } else {
      // Antd definitions are missing `onClick` for step, even though it works.
      const Step = Steps.Step as any;
      content = (
        <div className="CCRFlow">
          <div className="CCRFlow-header">
            <Steps current={currentIndex}>
              {STEP_ORDER.slice(0, 3).map(s => (
                <Step
                  key={s}
                  title={STEP_INFO[s].short}
                  onClick={() => this.setStep(s)}
                  style={{ cursor: 'pointer' }}
                />
              ))}
            </Steps>
            <h1 className="CCRFlow-header-title">{info.title}</h1>
            <div className="CCRFlow-header-subtitle">{info.subtitle}</div>
          </div>
          <div className="CCRFlow-content">
            <StepComponent
              proposalId={this.props.form && this.props.form.ccrId}
              initialState={this.props.form}
              updateForm={this.debouncedUpdateForm}
              setStep={this.setStep}
            />
          </div>
        </div>
      );
    }

    return (
      <div>
        {content}
        {showFooter && (
          <div className="CCRFlow-footer">
            {isLastStep ? (
              <>
                <button
                  className="CCRFlow-footer-button"
                  key="preview"
                  onClick={this.togglePreview}
                >
                  {isPreviewing ? 'Back to Edit' : 'Preview'}
                </button>
                <button
                  className="CCRFlow-footer-button is-primary"
                  key="submit"
                  onClick={this.openPublishWarning}
                  disabled={this.checkFormErrors()}
                >
                  Submit
                </button>
              </>
            ) : (
              <>
                <div className="CCRFlow-footer-help">{info.help}</div>
                <button
                  className="CCRFlow-footer-button"
                  key="next"
                  onClick={this.nextStep}
                >
                  Continue <Icon type="right-circle-o" />
                </button>
              </>
            )}
          </div>
        )}
        {isSavingDraft ? (
          <div className="CCRFlow-draftNotification">Saving draft...</div>
        ) : (
          saveDraftError && (
            <div className="CCRFlow-draftNotification is-error">
              Failed to save draft!
              <br />
              {saveDraftError}
            </div>
          )
        )}
        <CCRSubmitWarningModal
          ccr={this.props.form}
          isVisible={isShowingSubmitWarning}
          handleClose={this.closePublishWarning}
          handleSubmit={this.startSubmit}
        />
      </div>
    );
  }

  private updateForm = (form: Partial<CCRDraft>) => {
    this.props.updateCCRForm(form);
  };

  private setStep = (step: CCR_STEP, skipHistory?: boolean) => {
    this.setState({ step });
    if (!skipHistory) {
      const { history, location } = this.props;
      history.push(`${location.pathname}?step=${step.toLowerCase()}`);
    }
  };

  private nextStep = () => {
    const idx = STEP_ORDER.indexOf(this.state.step);
    if (idx !== STEP_ORDER.length - 1) {
      this.setStep(STEP_ORDER[idx + 1]);
    }
  };

  private togglePreview = () => {
    this.setState({ isPreviewing: !this.state.isPreviewing });
  };

  private startSubmit = () => {
    this.setState({
      isSubmitting: true,
      isShowingSubmitWarning: false,
    });
  };

  private checkFormErrors = () => {
    if (!this.props.form) {
      return true;
    }
    const errors = getCCRErrors(this.props.form);
    return !!Object.keys(errors).length;
  };

  private handlePop: History.LocationListener = (location, action) => {
    if (action === 'POP') {
      this.setState({ isPreviewing: false });
      const searchValues = qs.parse(location.search);
      const urlStep = searchValues.step && searchValues.step.toUpperCase();
      if (urlStep && CCR_STEP[urlStep]) {
        this.setStep(urlStep as CCR_STEP, true);
      } else {
        this.setStep(CCR_STEP.BASICS, true);
      }
    }
  };

  private openPublishWarning = () => {
    this.setState({ isShowingSubmitWarning: true });
  };

  private closePublishWarning = () => {
    this.setState({ isShowingSubmitWarning: false });
  };

  private cancelSubmit = () => {
    this.setState({ isSubmitting: false });
  };
}

const withConnect = connect<StateProps, DispatchProps, {}, AppState>(
  (state: AppState) => ({
    form: state.ccr.form,
    isSavingDraft: state.ccr.isSavingDraft,
    hasSavedDraft: state.ccr.hasSavedDraft,
    saveDraftError: state.ccr.saveDraftError,
  }),
  {
    updateCCRForm: ccrActions.updateCCRForm,
  },
);

export default compose<Props, {}>(
  withRouter,
  withConnect,
)(CCRFlow);
