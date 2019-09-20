import PropTypes from 'prop-types';
import React from 'react';
import _ from 'lodash';

import InstallPromptBanner from 'app/views/organizationDetails/installPromptBanner';

import SentryTypes from 'app/sentryTypes';
import withApi from 'app/utils/withApi';
import withTeamsForUser from 'app/utils/withTeamsForUser';

class LightWeightInstallPromptBanner extends React.Component {
  static propTypes = {
    organization: SentryTypes.Organization,
    teams: PropTypes.arrayOf(SentryTypes.Team),
    loadingTeams: PropTypes.bool,
    error: PropTypes.instanceOf(Error),
  };

  render() {
    if (this.props.loadingTeams || this.props.error) {
      return null;
    }
    return (
      <InstallPromptBanner
        {...this.props}
        projects={_.uniq(_.flatten(this.props.teams.map(team => team.projects)), 'id')}
      />
    );
  }
}

export default withApi(withTeamsForUser(LightWeightInstallPromptBanner));
