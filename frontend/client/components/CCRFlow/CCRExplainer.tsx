import React from 'react';
import { withNamespaces, WithNamespaces } from 'react-i18next';
import SubmitIcon from 'static/images/guide-submit.svg';
import ReviewIcon from 'static/images/guide-review.svg';
import CommunityIcon from 'static/images/guide-community.svg';
import './CCRExplainer.less';
import * as ls from 'local-storage';
import { Button, Checkbox, Icon } from 'antd';

interface CreateProps {
  startSteps: () => void;
}

type Props = WithNamespaces & CreateProps;

const CCRExplainer: React.SFC<Props> = ({ t, startSteps }) => {
  const items = [
    {
      text: t('home.guide.submit'),
      icon: <SubmitIcon />,
    },
    {
      text: t('home.guide.review'),
      icon: <ReviewIcon />,
    },
    {
      text: t('home.guide.community'),
      icon: <CommunityIcon />,
    },
  ];

  return (
    <div className="CCRExplainer">
      <div className="CCRExplainer-header">
        <h2 className="CCRExplainer-header-title">{t('home.guide.title')}</h2>
        <div className="CCRExplainer-header-subtitle">
          You're almost ready to create a proposal.
        </div>
      </div>
      <div className="CCRExplainer-items">
        {items.map((item, idx) => (
          <div className="CCRExplainer-items-item" key={idx}>
            <div className="CCRExplainer-items-item-icon">{item.icon}</div>
            <div className="CCRExplainer-items-item-text">{item.text}</div>
          </div>
        ))}
      </div>
      <div className="CCRExplainer-actions">
        <Checkbox onChange={ev => ls.set<boolean>('noExplain', ev.target.checked)}>
          Don't show this again
        </Checkbox>
        <Button
          className="CCRExplainer-create"
          type="primary"
          size="large"
          block
          onClick={() => startSteps()}
        >
          Let's do this <Icon type="right-circle-o" />
        </Button>
      </div>
    </div>
  );
};

export default withNamespaces()(CCRExplainer);
