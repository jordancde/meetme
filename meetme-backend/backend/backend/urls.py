from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework import routers

from django.urls import path, include
from django.contrib import admin
from django.conf.urls import include, url

from django.views.decorators.csrf import csrf_exempt

import oauth2_provider.views as oauth2_views

from backend import settings

from meet_me import views

admin.autodiscover()

# OAuth2 provider endpoints
oauth2_endpoint_views = [
    url(r'^authorize/$', oauth2_views.AuthorizationView.as_view(), name="authorize"),
    url(r'^token/$', oauth2_views.TokenView.as_view(), name="token"),
    url(r'^revoke-token/$', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
]


if settings.DEBUG:
    # OAuth2 Application Management endpoints
    oauth2_endpoint_views += [
        url(r'^applications/$', oauth2_views.ApplicationList.as_view(), name="list"),
        url(r'^applications/register/$',
            oauth2_views.ApplicationRegistration.as_view(), name="register"),
        url(r'^applications/(?P<pk>\d+)/$',
            oauth2_views.ApplicationDetail.as_view(), name="detail"),
        url(r'^applications/(?P<pk>\d+)/delete/$',
            oauth2_views.ApplicationDelete.as_view(), name="delete"),
        url(r'^applications/(?P<pk>\d+)/update/$',
            oauth2_views.ApplicationUpdate.as_view(), name="update"),
    ]

    # OAuth2 Token Management endpoints
    oauth2_endpoint_views += [
        url(r'^authorized-tokens/$', oauth2_views.AuthorizedTokensListView.as_view(),
            name="authorized-token-list"),
        url(r'^authorized-tokens/(?P<pk>\d+)/delete/$', oauth2_views.AuthorizedTokenDeleteView.as_view(),
            name="authorized-token-delete"),
    ]

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^v1/api/users/$', views.MeetMeUserListView.as_view(), name="users_list"),
    url(r'^v1/api/users/(?P<pk>\d+)/slots/$', views.SlotsListView.as_view(), name="slots_list"),
    url(r'^v1/api/users/(?P<pk>\d+)/requests/$', views.RequestsListView.as_view(), name="requests_list"),
    url(r'^v1/api/users/(?P<pk>\d+)/meetings/$', views.MeetingsListView.as_view(), name="meetings_list"),

    url(r'^v1/api/users/(?P<pk>\d+)/$', views.MeetMeUserDetailsView.as_view(), name="user_details"),
]
urlpatterns = format_suffix_patterns(urlpatterns)
