import React from 'react';
import { withRouter, RouteComponentProps } from 'react-router';
// import DraftList from 'components/DraftList';

type Props = RouteComponentProps<{}>;

class CreateRequestPage extends React.Component<Props> {
  render() {
    return (
      <>
        <noscript className="noScript is-block">
          Community Request creation requires Javascript. You’ll need to enable it to continue.
        </noscript>
          <h1>Hi! This is the CCR view</h1>
        {/*<DraftList createIfNone createWithRfpId />*/}
      </>
    );
  }
}

export default withRouter(CreateRequestPage);
