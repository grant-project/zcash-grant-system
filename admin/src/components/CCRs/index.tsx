import React from 'react';
import { view } from 'react-easy-state';
import { Button, List, Popconfirm, Spin, Tag, Tooltip, message } from 'antd';
import { RouteComponentProps, withRouter } from 'react-router';
import { Link } from 'react-router-dom';
import { CCR_STATUSES, getStatusById } from 'util/statuses';
import store from 'src/store';
import './index.less';
import { CCR } from 'src/types';
import {formatDateSeconds} from "util/time";

type Props = RouteComponentProps<any>;

interface State {
  deletingId: number | null;
}

class CCRs extends React.Component<Props, State> {
  state: State = {
    deletingId: null,
  };

  componentDidMount() {
    this.fetchCCRs();
  }

  render() {
    const { ccrs, ccrsFetching, ccrsFetched } = store;
    const loading = !ccrsFetched || ccrsFetching;

    return (
      <div className="CCRs">
        <div className="CCRs-controls">
          <Button title="refresh" icon="reload" onClick={this.fetchCCRs} />
        </div>
        <List
          className="CCRs-list"
          bordered
          dataSource={ccrs}
          loading={loading}
          renderItem={this.renderCCR}
        />
      </div>
    );
  }

  private fetchCCRs = () => {
    store.fetchCCRs();
  };

  private renderCCR = (ccr: CCR) => {
    const { deletingId } = this.state;
    const actions = [
      <Popconfirm
        key="delete"
        title="Are you sure?"
        okText="Delete"
        okType="danger"
        onConfirm={() => this.deleteCCR(ccr.ccrId)}
        placement="left"
      >
        <a>delete</a>
      </Popconfirm>,
    ];
    const status = getStatusById(CCR_STATUSES, ccr.status);
    return (
      <Spin key={ccr.ccrId} spinning={deletingId === ccr.ccrId}>
        <List.Item className="CCRs-list-ccr" actions={actions}>
          <Link to={`/ccrs/${ccr.ccrId}`}>
            <h2>
              {ccr.title || '(no title)'}
              <Tooltip title={status.hint}>
                <Tag color={status.tagColor}>{status.tagDisplay}</Tag>
              </Tooltip>
            </h2>
            <p>Created: {formatDateSeconds(ccr.dateCreated)}</p>
            <p>{ccr.brief}</p>
          </Link>
        </List.Item>
      </Spin>
    );
  };

  private deleteCCR = (id: number) => {
    this.setState({ deletingId: id }, async () => {
      await store.deleteCCR(id);
      if (store.ccrDeleted) {
        message.success('Successfully deleted', 2);
      }
      this.setState({ deletingId: null });
    });
  };
}

export default withRouter(view(CCRs));
