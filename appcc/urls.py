# -*- coding: utf-8 -*-

from django.conf.urls import include,url
from django.conf.urls import patterns
from django.conf import settings


from django.contrib import admin
from rest_framework import routers
import views_app,views
from rest_framework.authtoken.views import obtain_auth_token
from account.decorators import login_exempt


routers=routers.DefaultRouter()
routers.register(r'app',views_app.ApplicationViewSet)
routers.register(r'package',views_app.PackageViewSet)
routers.register(r'version',views_app.VersionViewSet)


urlpatterns = patterns('appcc.views',
                       (r'^$', 'home'),
                       (r'^base_main','base_main'),
                       (r'^home', 'home'),
                       #appdelivery
                        (r'^app_delivery/$', 'app_list'),
                       (r'app_delivery/applist/(?P<app_id>(\d+))/$','applists'),
                       (r'^main_deploy', 'app_info'),
                       (r'^app_deploy','app_deploy'),
                       (r'^deploy_maintain','deploy_maintain'),
                       (r'^deploy_historytask','deploy_historytask'),
                       #tool
                         (r'^tool_list','tool_list'),
                       (r'^create_tool','create_tool'),
                       (r'^tool_info','tool_info'),
                       (r'^run_tool','run_tool'),
                       (r'^edit_tool','edit_tool'),
                       (r'^conf_tool','conf_tool'),
                       (r'^tool_history','tool_history'),
                       #flow
                         (r'^flow_list','flow_list'),
                       (r'^flow_orch','flow_orch'),
                       (r'^history_flow','history_flow'),
                       #timetask
                        (r'^time_task','time_tasklist'),
                       (r'^create_timetask','create_timetask'),
                       #CI
                        (r'^construct_rep','construct_rep'),
                       (r'^soft_package','soft_package'),
                       (r'^conf_package','conf_package'),
                       (r'^jenkinsCI','jenkinsCI'),
                       (r'^jenkins_newitem','jenkins_newitem'),
                       (r'^jenkins_publish_statistics', 'jenkins_publish_statistics'),
                       (r'^jenkins_newjob','jenkins_newjob'),
                        (r'^jenkins_app_build/(?P<app_name>.+)', 'jenkins_app_build'),
                        (r'^jenkins_app_build_check_status/(?P<app_name>.+)', 'jenkins_app_build_check_status'),
                       (r'^jenkins_app_change_config', 'jenkins_app_change_config'),
                        (r'^jenkins_app_stop/(?P<app_name>.+)', 'jenkins_app_stop'),
                       (r'^create_soft','create_soft'),
                       (r'^create_conf','create_conf'),
                       (r'^package_info','package_info'),
                       (r'^application/$', views_app.applition_list),
                       (r'^api', include(routers.urls)),
                       (r'^applist', 'app_list'),

                       )
urlpatterns += patterns('appcc.views_app',
                       ),

