import React from 'react';
import { Form, Input, Button, message } from 'antd';
import { updateUserSettings } from 'api/api';
import { isValidAddress } from 'utils/validators';
import { UserSettings } from 'types';

interface Props {
  userSettings?: UserSettings;
  isFetching: boolean;
  errorFetching: boolean;
  userid: number;
  onAddressSet: (refundAddress: UserSettings['tipJarAddress']) => void;
}


interface State {
  isSaving: boolean
  tipJarAddress: string | null
  tipJarAddressSet: string | null
}

export default class TipJarAddress extends React.Component<Props, State> {

  static getDerivedStateFromProps(nextProps: Props, prevState: State) {
    const { userSettings } = nextProps;
    const { tipJarAddress, tipJarAddressSet } = prevState;

    const ret: Partial<State> = {};

    if (!userSettings || !userSettings.tipJarAddress) {
      return ret;
    }

    if (userSettings.tipJarAddress !== tipJarAddressSet) {
      ret.tipJarAddressSet = userSettings.tipJarAddress;

      if (tipJarAddress === null) {
        ret.tipJarAddress = userSettings.tipJarAddress;
      }
    }

    return ret;
  }
  
  state: State = { 
    isSaving: false,
    tipJarAddress: null,
    tipJarAddressSet: null
   };

  render() {
    const { isSaving, tipJarAddress, tipJarAddressSet } = this.state;
    const { isFetching, errorFetching } = this.props;
    const addressChanged = tipJarAddress !== tipJarAddressSet;

    let status: 'validating' | 'error' | undefined;
    let help;
    if (isFetching) {
      status = 'validating';
    } else if (tipJarAddress && !isValidAddress(tipJarAddress)) {
      status = 'error';
      help = 'That doesn’t look like a valid address';
    }

    return (
      <Form className="RefundAddress" layout="vertical" onSubmit={this.handleSubmit}>
        <Form.Item label="Tip jar address" validateStatus={status} help={help}>
          <Input
            value={tipJarAddress || ''}
            placeholder="Z or T address"
            onChange={this.handleChange}
            disabled={isFetching || isSaving || errorFetching}
          />
        </Form.Item>

        <Button
          type="primary"
          htmlType="submit"
          size="large"
          disabled={
            !tipJarAddress || isSaving || !!status || errorFetching || !addressChanged
          }
          loading={isSaving}
          block
        >
          Change tip jar address
        </Button>
      </Form>
    );
  }

  private handleChange = (ev: React.ChangeEvent<HTMLInputElement>) => {
    this.setState({ tipJarAddress: ev.currentTarget.value });
  };

  private handleSubmit = async (ev: React.FormEvent<HTMLFormElement>) => {
    ev.preventDefault();
    const { userid } = this.props;
    const { tipJarAddress } = this.state;
    if (!tipJarAddress) {
      return;
    }

    this.setState({ isSaving: true });
    try {
      const res = await updateUserSettings(userid, { tipJarAddress });
      message.success('Settings saved');
      const tipJarAddressNew = res.data.tipJarAddress || '';
      this.setState({ tipJarAddress: tipJarAddressNew });
      this.props.onAddressSet(tipJarAddressNew);
    } catch (err) {
      console.error(err);
      message.error(err.message || err.toString(), 5);
    }
    this.setState({ isSaving: false });
  };
}
