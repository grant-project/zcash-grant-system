import React from 'react';
import { Modal, Icon, Button, Form, Input } from 'antd';
import classnames from 'classnames';
import QRCode from 'qrcode.react';
import { formatZcashCLI, formatZcashURI } from 'utils/formatters';
import Loader from 'components/Loader';
import './TipJarModal.less';
import CopyInput from 'components/CopyInput';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  type: 'user' | 'proposal';
  address: string;
}

const STATE = {
  amount: '0',
};
type State = typeof STATE;

export default class TipJarModal extends React.Component<Props, State> {
  state = STATE;

  render() {
    const { isOpen, onClose, type, address } = this.props;
    const { amount } = this.state;

    const amountIsValid = this.simpleAmountValidate(amount)

    const cli = amountIsValid ? formatZcashCLI(address, amount) : ''
    const uri = amountIsValid ? formatZcashURI(address, amount) : ''

    const content = (
      <div className="TipJarModal">
        <div className="TipJarModal-uri">
          <div>
            <div className={classnames('TipJarModal-uri-qr', !uri && 'is-loading')}>
              <span style={{ opacity: uri ? 1 : 0 }}>
                <QRCode value={uri || ''} />
              </span>
              {!uri && <Loader />}
            </div>
          </div>
          <div className="TipJarModal-uri-info">
            <Form.Item
              validateStatus={amountIsValid ? undefined : 'error'}
              label="Amount"
              className="TipJarModal-uri-info-input CopyInput"
            >
              <Input
                type="number"
                value={amount}
                placeholder="Amount to send"
                onChange={this.handleAmountChange}
                addonAfter="ZEC"
              />
            </Form.Item>
            <CopyInput
              className="TipJarModal-uri-info-input"
              label="Payment URI"
              value={uri}
              isTextarea
            />
            <Button type="ghost" size="large" href={uri} block>
              Open in Wallet <Icon type="link" />
            </Button>
          </div>
        </div>

        <div className="TipJarModal-fields">
          <div className="TipJarModal-fields-row">
            <CopyInput
              className="TipJarModal-fields-row-address"
              label="Address"
              value={address}
            />
          </div>
          <div className="TipJarModal-fields-row">
            <CopyInput
              label="Zcash CLI command"
              help="Make sure you replace YOUR_ADDRESS with your actual address"
              value={cli}
            />
          </div>
        </div>
      </div>
    );
    return (
      <Modal
        title={`Tip a ${type}`}
        visible={isOpen}
        okText={'Done'}
        centered
        footer={
          <Button type="primary" onClick={onClose}>
            Done
          </Button>
        }
      >
        {content}
      </Modal>
    );
  }

  private handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    this.setState({
      amount: e.currentTarget.value,
    });

  private simpleAmountValidate = (amount: string) => {
    const target = parseFloat(amount)
    if (Number.isNaN(target)) {
      return false
    }
    if (target < 0) {
      return false
    }
    // prevents "-0" from being valid...
    if (amount[0] === '-') {
      return false
    }
    return true
  };
}
