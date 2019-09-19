from __future__ import absolute_import

from django.utils.translation import ugettext_lazy as _

from sentry.utils import json
from sentry.integrations import (
    IntegrationInstallation,
    IntegrationFeatures,
    IntegrationMetadata,
    IntegrationProvider,
    FeatureDescription,
)
from sentry.models import PagerDutyServiceProject, Project
from sentry.pipeline import PipelineView

DESCRIPTION = """
PagerDuty Description
"""

FEATURES = [
    FeatureDescription(
        """
        Configure rule based PagerDuty notifications!!
        """,
        IntegrationFeatures.ALERT_RULE,
    )
]

metadata = IntegrationMetadata(
    description=_(DESCRIPTION.strip()),
    features=FEATURES,
    author="The Sentry Team",
    noun=_("Installation"),
    issue_url="https://github.com/getsentry/sentry/issues/new?title=Slack%20Integration:%20&labels=Component%3A%20Integrations",
    source_url="https://github.com/getsentry/sentry/tree/master/src/sentry/integrations/slack",
    aspects={},
)


class PagerDutyIntegration(IntegrationInstallation):
    def get_client(self):
        pass

    def get_organization_config(self):
        from sentry.models import Project

        projects = Project.objects.filter(
            organization_id__in=self.model.organizations.values_list("id", flat=True)
        )
        items = []
        for p in projects:
            items.append({"value": p.id, "label": p.name})

        service_options = [(s['id'], s['name'],) for s in self.services.values()]

        fields = [
            {
                "name": "project_mapping",
                "type": "choice_mapper",
                "label": _("Map projects in Sentry to services in PagerDuty"),
                "help": _(
                    "When an alert rule is triggered in a project, this mapping will let us know what service to create the incident in PagerDuty."
                ),
                "addButtonText": _("Add Sentry Project"),
                "addDropdown": {
                    "emptyMessage": _("All projects configured"),
                    "noResultsMessage": _("Could not find project"),
                    "items": items,
                },
                "mappedSelectors": {
                    "service": {
                        "choices": service_options,
                        "placeholder": _("Select a service"),
                    }
                },
                "columnLabels": {"service": _("Service")},
                "mappedColumnLabel": _("Sentry Project"),
            }
        ]

        return fields

    def update_organization_config(self, data):

        if "project_mapping" in data:
            project_ids_and_services = data.pop("project_mapping")

            PagerDutyServiceProject.objects.filter(
                organization_integration_id=self.org_integration.id,
            ).delete()

            for p_id, s in project_ids_and_services.items():
                # create the record in the table
                project = Project.objects.get(pk=p_id)
                service = self.services[s['service']]
                PagerDutyServiceProject.objects.create(
                    organization_integration=self.org_integration,
                    project=project,
                    service_name=service['name'],
                    service_id=service['id'],
                    integration_key=service['integration_key'],
                )

    def get_config_data(self):
        config = self.org_integration.config
        project_mappings = PagerDutyServiceProject.objects.filter(
            organization_integration_id=self.org_integration.id
        )
        data = {}
        for pm in project_mappings:
            data[pm.project_id] = {
                "service": pm.service_id,
            }
            print(pm.service_name)
        config = {}
        config["project_mapping"] = data
        return config

    @property
    def services(self):
        return self.model.metadata['services']


class PagerDutyIntegrationProvider(IntegrationProvider):
    key = "pagerduty"
    name = "PagerDuty"
    metadata = metadata
    features = frozenset([IntegrationFeatures.ALERT_RULE])
    integration_cls = PagerDutyIntegration

    setup_dialog_config = {"width": 600, "height": 900}

    def get_pipeline_views(self):
        return [PagerDutyInstallationRedirect()]

    def build_integration(self, state):
        config = json.loads(state.get("config"))
        account = config["account"]

        return {
            # should be account["name"] when pg updates it
            "name": account["subdomain"],
            "external_id": account["subdomain"],
            # make it easy to get a service in format of
            #   "service_id": {
            #       "integration_key": <key>.
            #       "service_name": <name>,
            #       "service_id": <id>,
            #   }
            # note: integration_keys has keys for things other than services
            "metadata": {"services": dict([(s['id'], s) for s in config['integration_keys']])},
        }


class PagerDutyInstallationRedirect(PipelineView):
    def get_app_url(self):
        return "https://app.pagerduty.com/install/integration?app_id=PZNIQIG&redirect_url=https://meredith.ngrok.io/extensions/pagerduty/setup/&version=1"

    def dispatch(self, request, pipeline):
        if "config" in request.GET:
            pipeline.bind_state("config", request.GET["config"])
            return pipeline.next_step()

        return self.redirect(self.get_app_url())
