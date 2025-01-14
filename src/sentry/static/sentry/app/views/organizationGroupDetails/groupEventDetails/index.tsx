import React from 'react';

import {fetchOrganizationEnvironments} from 'app/actionCreators/environments';
import {t} from 'app/locale';
import GroupEventDetails from 'app/views/organizationGroupDetails/groupEventDetails/groupEventDetails';
import LoadingError from 'app/components/loadingError';
import LoadingIndicator from 'app/components/loadingIndicator';
import OrganizationEnvironmentsStore from 'app/stores/organizationEnvironmentsStore';
import {Client} from 'app/api';
import {GlobalSelection, Organization, Environment} from 'app/types';
import withApi from 'app/utils/withApi';
import withGlobalSelection from 'app/utils/withGlobalSelection';
import withOrganization from 'app/utils/withOrganization';

type Props = {
  api: Client;
  organization: Organization;
  selection: GlobalSelection;
};

type State = {
  environments: Environment[];
  error: Error;
};

export class GroupEventDetailsContainer extends React.Component<Props, State> {
  state = OrganizationEnvironmentsStore.get();

  componentDidMount() {
    this.environmentSubscription = OrganizationEnvironmentsStore.listen(data =>
      this.setState(data)
    );
    const {environments, error} = OrganizationEnvironmentsStore.get();
    if (!environments && !error) {
      fetchOrganizationEnvironments(this.props.api, this.props.organization.slug);
    }
  }

  componentWillUnmount() {
    if (this.environmentSubscription) {
      this.environmentSubscription.unsubscribe();
    }
  }

  // TODO(ts): reflux :(
  environmentSubscription: any;

  render() {
    if (this.state.error) {
      return (
        <LoadingError
          message={t("There was an error loading your organization's environments")}
        />
      );
    }
    // null implies loading state
    if (!this.state.environments) {
      return <LoadingIndicator />;
    }
    const {selection, ...otherProps} = this.props;
    const environments = this.state.environments.filter(env =>
      selection.environments.includes(env.name)
    );
    return <GroupEventDetails {...otherProps} environments={environments} />;
  }
}

export default withApi(withOrganization(withGlobalSelection(GroupEventDetailsContainer)));
