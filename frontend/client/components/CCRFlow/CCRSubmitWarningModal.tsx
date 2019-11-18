import React from 'react';
import { Modal } from 'antd';
import { CCRDraft } from 'types';
import './CCRSubmitWarningModal.less';

interface Props {
  ccr: CCRDraft | null;
  isVisible: boolean;
  handleClose(): void;
  handleSubmit(): void;
}

export default class CCRSubmitWarningModal extends React.Component<Props> {
  render() {
    const { ccr, isVisible, handleClose, handleSubmit } = this.props;

    const staked = ccr && ccr.isStaked;

    return (
      <Modal
        title={<>Confirm submission</>}
        visible={isVisible}
        okText={staked ? 'Submit' : `I'm ready to stake`}
        cancelText="Never mind"
        onOk={handleSubmit}
        onCancel={handleClose}
      >
        <div className="CCRSubmitWarningModal">
          {staked && (
            <p>
              Are you sure you're ready to submit your request for approval? Once you’ve
              done so, you won't be able to edit it.
            </p>
          )}
          {!staked && (
            <p>
              Are you sure you're ready to submit your Request? You will be asked to send
              a staking contribution of <b>{process.env.CCR_STAKING_AMOUNT} ZEC</b>. Once
              confirmed, the request will be submitted for approval by site
              administrators.
            </p>
          )}
        </div>
      </Modal>
    );
  }
}
