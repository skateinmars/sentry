import React from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/lib/Modal';
import styled from 'react-emotion';

import withApi from 'app/utils/withApi';
import InlineSvg from 'app/components/inlineSvg';
import {addSuccessMessage, addErrorMessage} from 'app/actionCreators/indicator';
import {IntegrationLink} from 'app/components/issueSyncListElement';
import SentryAppIcon from 'app/components/sentryAppIcon';
import SentryAppExternalIssueForm from 'app/components/group/sentryAppExternalIssueForm';
import NavTabs from 'app/components/navTabs';
import {t, tct} from 'app/locale';
import SentryTypes from 'app/sentryTypes';
import space from 'app/styles/space';
import {deleteExternalIssue} from 'app/actionCreators/platformExternalIssues';

class SentryAppExternalIssueActions extends React.Component {
  static propTypes = {
    api: PropTypes.object.isRequired,
    group: PropTypes.object.isRequired,
    sentryAppComponent: PropTypes.object.isRequired,
    sentryAppInstallation: PropTypes.object,
    externalIssue: PropTypes.object,
    event: SentryTypes.Event,
  };

  constructor(props) {
    super(props);

    this.state = {
      action: 'create',
      externalIssue: props.externalIssue,
      showModal: false,
    };
  }

  componentDidUpdate(prevProps) {
    if (this.props.externalIssue !== prevProps.externalIssue) {
      this.updateExternalIssue(this.props.externalIssue);
    }
  }

  updateExternalIssue(externalIssue) {
    this.setState({externalIssue});
  }

  showModal = () => {
    // Only show the modal when we don't have a linked issue
    !this.state.externalIssue && this.setState({showModal: true});
  };

  hideModal = () => {
    this.setState({showModal: false});
  };

  showLink = () => {
    this.setState({action: 'link'});
  };

  showCreate = () => {
    this.setState({action: 'create'});
  };

  deleteIssue = () => {
    const {api, group} = this.props;
    const {externalIssue} = this.state;

    deleteExternalIssue(api, group.id, externalIssue.id)
      .then(data => {
        this.setState({externalIssue: null});
        addSuccessMessage(t('Successfully unlinked issue.'));
      })
      .catch(error => {
        addErrorMessage(t('Unable to unlink issue.'));
      });
  };

  onAddRemoveClick = () => {
    const {externalIssue} = this.state;

    if (!externalIssue) {
      this.showModal();
    } else {
      this.deleteIssue();
    }
  };

  onSubmitSuccess = externalIssue => {
    this.setState({externalIssue});
    this.hideModal();
  };

  get link() {
    const {sentryAppComponent} = this.props;
    const {externalIssue} = this.state;
    const name = sentryAppComponent.sentryApp.name;

    let url = '#';
    let displayName = tct('Link [name] Issue', {name});

    if (externalIssue) {
      url = externalIssue.webUrl;
      displayName = externalIssue.displayName;
    }

    return (
      <IssueLinkContainer>
        <IssueLink>
          <StyledSentryAppIcon slug={sentryAppComponent.sentryApp.slug} />
          <IntegrationLink onClick={this.showModal} href={url}>
            {displayName}
          </IntegrationLink>
        </IssueLink>
        <AddRemoveIcon
          src="icon-close"
          isLinked={!!externalIssue}
          onClick={this.onAddRemoveClick}
        />
      </IssueLinkContainer>
    );
  }

  get modal() {
    const {sentryAppComponent, sentryAppInstallation, group} = this.props;
    const {action, showModal} = this.state;
    const name = sentryAppComponent.sentryApp.name;

    return (
      <Modal show={showModal} onHide={this.hideModal} animation={false}>
        <Modal.Header closeButton>
          <Modal.Title>{tct('[name] Issue', {name})}</Modal.Title>
        </Modal.Header>
        <NavTabs underlined>
          <li className={action === 'create' ? 'active create' : 'create'}>
            <a onClick={this.showCreate}>{t('Create')}</a>
          </li>
          <li className={action === 'link' ? 'active link' : 'link'}>
            <a onClick={this.showLink}>{t('Link')}</a>
          </li>
        </NavTabs>
        <Modal.Body>
          <SentryAppExternalIssueForm
            group={group}
            sentryAppInstallation={sentryAppInstallation}
            config={sentryAppComponent.schema}
            action={action}
            onSubmitSuccess={this.onSubmitSuccess}
            event={this.props.event}
          />
        </Modal.Body>
      </Modal>
    );
  }

  render() {
    return (
      <React.Fragment>
        {this.link}
        {this.modal}
      </React.Fragment>
    );
  }
}

const StyledSentryAppIcon = styled(SentryAppIcon)`
  color: ${p => p.theme.gray4};
  width: ${space(3)};
  height: ${space(3)};
  cursor: pointer;
  flex-shrink: 0;
`;

const IssueLink = styled('div')`
  display: flex;
  align-items: center;
  min-width: 0;
`;

const IssueLinkContainer = styled('div')`
  line-height: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
`;

const AddRemoveIcon = styled(InlineSvg)`
  height: ${space(1.5)};
  color: ${p => p.theme.gray4};
  transition: 0.2s transform;
  cursor: pointer;
  box-sizing: content-box;
  padding: ${space(1)};
  margin: -${space(1)};
  ${p => (p.isLinked ? '' : 'transform: rotate(45deg) scale(0.9);')};
`;

export default withApi(SentryAppExternalIssueActions);
