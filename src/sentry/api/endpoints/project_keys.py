from __future__ import absolute_import

from django.db.models import F
from rest_framework import serializers, status
from rest_framework.response import Response

from sentry import features
from sentry.api.base import DocSection
from sentry.api.bases.project import ProjectEndpoint
from sentry.api.fields.empty_integer import EmptyIntegerField
from sentry.api.serializers import serialize
from sentry.models import AuditLogEntryEvent, ProjectKey, ProjectKeyStatus
from sentry.utils.apidocs import scenario, attach_scenarios


@scenario("ListClientKeys")
def list_keys_scenario(runner):
    runner.request(
        method="GET", path="/projects/%s/%s/keys/" % (runner.org.slug, runner.default_project.slug)
    )


@scenario("CreateClientKey")
def create_key_scenario(runner):
    runner.request(
        method="POST",
        path="/projects/%s/%s/keys/" % (runner.org.slug, runner.default_project.slug),
        data={"name": "Fabulous Key"},
    )


class RateLimitSerializer(serializers.Serializer):
    count = EmptyIntegerField(min_value=0, required=False, allow_null=True)
    window = EmptyIntegerField(min_value=0, max_value=60 * 60 * 24, required=False, allow_null=True)


class KeySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    public = serializers.RegexField(r"^[a-f0-9]{32}$", required=False, allow_null=True)
    secret = serializers.RegexField(r"^[a-f0-9]{32}$", required=False, allow_null=True)
    rateLimit = RateLimitSerializer(required=False, allow_null=True)


class ProjectKeysEndpoint(ProjectEndpoint):
    doc_section = DocSection.PROJECTS

    @attach_scenarios([list_keys_scenario])
    def get(self, request, project):
        """
        List a Project's Client Keys
        ````````````````````````````

        Return a list of client keys bound to a project.

        :pparam string organization_slug: the slug of the organization the
                                          client keys belong to.
        :pparam string project_slug: the slug of the project the client keys
                                     belong to.
        """
        queryset = ProjectKey.objects.filter(
            project=project, roles=F("roles").bitor(ProjectKey.roles.store)
        )
        status = request.GET.get("status")
        if status == "active":
            queryset = queryset.filter(status=ProjectKeyStatus.ACTIVE)
        elif status == "inactive":
            queryset = queryset.filter(status=ProjectKeyStatus.INACTIVE)
        elif status:
            queryset = queryset.none()

        return self.paginate(
            request=request,
            queryset=queryset,
            order_by="-id",
            on_results=lambda x: serialize(x, request.user),
        )

    @attach_scenarios([create_key_scenario])
    def post(self, request, project):
        """
        Create a new Client Key
        ```````````````````````

        Create a new client key bound to a project.  The key's secret and
        public key are generated by the server.

        :pparam string organization_slug: the slug of the organization the
                                          client keys belong to.
        :pparam string project_slug: the slug of the project the client keys
                                     belong to.
        :param string name: the name for the new key.
        """
        serializer = KeySerializer(data=request.data)

        if serializer.is_valid():
            result = serializer.validated_data

            rate_limit_count = None
            rate_limit_window = None

            if features.has("projects:rate-limits", project):
                ratelimit = result.get("rateLimit", -1)
                if ratelimit != -1 and (ratelimit["count"] and ratelimit["window"]):
                    rate_limit_count = result["rateLimit"]["count"]
                    rate_limit_window = result["rateLimit"]["window"]

            key = ProjectKey.objects.create(
                project=project,
                label=result.get("name"),
                public_key=result.get("public"),
                secret_key=result.get("secret"),
                rate_limit_count=rate_limit_count,
                rate_limit_window=rate_limit_window,
            )

            self.create_audit_entry(
                request=request,
                organization=project.organization,
                target_object=key.id,
                event=AuditLogEntryEvent.PROJECTKEY_ADD,
                data=key.get_audit_log_data(),
            )

            return Response(serialize(key, request.user), status=201)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
