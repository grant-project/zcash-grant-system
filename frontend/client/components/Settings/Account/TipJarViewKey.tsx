import React from 'react';
import { Form, Input, Button, message } from 'antd';
import { updateUserSettings } from 'api/api';
import { UserSettings } from 'types';

interface Props {
  userSettings?: UserSettings;
  isFetching: boolean;
  errorFetching: boolean;
  userid: number;
  onViewKeySet: (viewKey: UserSettings['tipJarViewKey']) => void;
}

const STATE = {
  isSaving: false,
  tipJarViewKey: '',
  tipJarViewKeyRemote: '',
};

type State = typeof STATE;

export default class TipJarViewKey extends React.Component<Props, State> {
  state: State = { ...STATE };

  static getDerivedStateFromProps(nextProps: Props, prevState: State) {
    const { userSettings } = nextProps;
    const { tipJarViewKey, tipJarViewKeyRemote } = prevState;

    let ret: Partial<State> = {};

    if (!userSettings || !userSettings.tipJarViewKey) {
      return ret;
    }

    if (userSettings.tipJarViewKey !== tipJarViewKeyRemote) {
      ret.tipJarViewKeyRemote = userSettings.tipJarViewKey;

      if (!tipJarViewKey) {
        ret.tipJarViewKey = userSettings.tipJarViewKey;
      }
    }

    return ret;
  }

  render() {
    const { isSaving, tipJarViewKey, tipJarViewKeyRemote } = this.state;
    const { isFetching, errorFetching, userSettings } = this.props;
    const viewKeyChanged = tipJarViewKey !== tipJarViewKeyRemote;
    const viewKeyDisabled = !(userSettings && userSettings.tipJarAddress);

    // TODO: add view key validation

    // let status: 'validating' | 'error' | undefined;
    // let help;
    // if (isFetching) {
    // status = 'validating';
    // } else if (tipJarAddress && !isValidAddress(tipJarAddress)) {
    // status = 'error';
    // help = 'That doesn’t look like a valid address';
    // }

    return (
      <Form className="RefundAddress" layout="vertical" onSubmit={this.handleSubmit}>
        <Form.Item label="Tip jar view key">
          <Input
            value={tipJarViewKey}
            placeholder="A view key for your tip jar address (optional)"
            onChange={this.handleChange}
            disabled={viewKeyDisabled || isFetching || isSaving || errorFetching}
          />
        </Form.Item>

        <Button
          type="primary"
          htmlType="submit"
          size="large"
          disabled={
            !tipJarViewKey || isSaving || !!status || errorFetching || !viewKeyChanged
          }
          loading={isSaving}
          block
        >
          Change tip jar view key
        </Button>
      </Form>
    );
  }

  private handleChange = (ev: React.ChangeEvent<HTMLInputElement>) => {
    this.setState({ tipJarViewKey: ev.currentTarget.value });
  };

  private handleSubmit = async (ev: React.FormEvent<HTMLFormElement>) => {
    ev.preventDefault();
    const { userid } = this.props;
    const { tipJarViewKey } = this.state;
    if (!tipJarViewKey) {
      return;
    }

    this.setState({ isSaving: true });
    try {
      const res = await updateUserSettings(userid, { tipJarViewKey });
      message.success('Settings saved');
      const tipJarViewKeyNew = res.data.tipJarViewKey || '';
      this.setState({ tipJarViewKey: tipJarViewKeyNew });
      this.props.onViewKeySet(tipJarViewKeyNew);
    } catch (err) {
      console.error(err);
      message.error(err.message || err.toString(), 5);
    }
    this.setState({ isSaving: false });
  };
}
