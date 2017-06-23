# -*- coding: utf-8 -*-

from account.decorators import login_exempt
from common.mymako import render_mako_context
from models import ApplicationInfo,Package,Jenkins
from django.shortcuts import render
import pycurl,StringIO,re,jenkins,json
import xml.dom.minidom, time, datetime, models, sys
from django.http import HttpResponse
from xml.etree import ElementTree as ET
import chardet


def app_list(request):
    app_list=ApplicationInfo.objects.values('appname','devleader','testleader','opsleader','lasttime')
    return render_mako_context(request,'/appcc/appdelivery/appdelivery.html',{
        'app_list': app_list
    })

def app_info(request):
    app_info=ApplicationInfo.objects.values('devleader','testleader','opsleader','numcluster','numhost','numsoftpack','numconfpack').filter(appname__contains='crm')
    soft_list=Package.objects.values('name','path','cversion').filter(type=0)
    conf_list=Package.objects.values('name','path','envfile','cversion').filter(type=1)
    return render_mako_context(request,'/appcc/appdelivery/maindeploy.html',{
        'app_info':app_info,
        'soft_list':soft_list,
        'conf_list':conf_list,

    })




def home(request):
    """
    首页1
    """
    return render_mako_context(request, '/appcc/cdmain.html')


@login_exempt
def app_delivery(request):
    """
    应用交付2
    """

    return render_mako_context(request, '/appcc/appdelivery/appdelivery.html')

@login_exempt
def main_deploy(request):
    """
    应用交付-->部署主页面3
    """
    return render_mako_context(request, '/appcc/appdelivery/maindeploy.html')


def base_main(request):
    return render_mako_context(request, '/appcc/base.html')


@login_exempt
def app_deploy(request):
    """
    应用交付-->功能：部署4
    """
    return render_mako_context(request, '/appcc/appdelivery/appdeploy.html')


@login_exempt
def deploy_maintain(request):
    """
    应用交付-->功能：维护5
    """
    return render_mako_context(request, '/appcc/appdelivery/maintain.html')


@login_exempt
def deploy_historytask(request):
    """
    应用交付-->功能：历史任务6
    """
    return render_mako_context(request, '/appcc/appdelivery/historytask.html')


@login_exempt
def delivery_tool(request):
    """
    交付工具7
    """
    return render_mako_context(request, '/appcc/deliverytool/toollist.html')


@login_exempt
def tool_list(request):
    """
    交付工具清单7
    """
    return render_mako_context(request, '/appcc/deliverytool/toollist.html')


@login_exempt
def tool_history(request):
    """
    交付工具—历史任务
    """
    return render_mako_context(request, '/appcc/deliverytool/toolhistory.html')


@login_exempt
def create_tool(request):
    """
    交付工具-->创建工具8
    """
    return render_mako_context(request, '/appcc/deliverytool/createtool.html')


@login_exempt
def tool_info(request):
    """
    交付工具-->工具详情9
    """
    return render_mako_context(request, '/appcc/deliverytool/toolinfo.html')


@login_exempt
def tool_baseinfo(request):
    """
    交付工具-->工具基本信息10
    """
    return render_mako_context(request, '/appcc/deliverytool/toolbaseinfo.html')


@login_exempt
def run_tool(request):
    """
    交付工具-->运行工具 11
    """
    return render_mako_context(request, '/appcc/deliverytool/runtool.html')


@login_exempt
def edit_tool(request):
    """
    交付工具-->编辑工具12
    """
    return render_mako_context(request, '/appcc/deliverytool/edittool.html')


@login_exempt
def conf_tool(request):
    """
    交付工具--工具高级配置13
    """
    return render_mako_context(request, '/appcc/deliverytool/conftool.html')


@login_exempt
def flow_schedule(request):
    """
    流程调度
    """
    return render_mako_context(request, '/appcc/flowschedule/flow.html')


@login_exempt
def flow_list(request):
    """
    流程列表14
    """
    return render_mako_context(request, '/appcc/flowschedule/flowlist.html')


@login_exempt
def flow_orch(request):
    """
    流程编排15
    """
    return render_mako_context(request, '/appcc/flowschedule/floworch.html')


@login_exempt
def history_flow(request):
    """
    定时任务16
    """
    return render_mako_context(request, '/appcc/flowschedule/historyflow.html')


@login_exempt
def time_tasklist(request):
    """
    定时任务16
    """
    return render_mako_context(request, '/appcc/timetask/timetasklist.html')


@login_exempt
def create_timetask(request):
    """
    定时任务16
    """
    return render_mako_context(request, '/appcc/timetask/createtimetask.html')


@login_exempt
def construct_rep(request):
    """
    构建集
    """
    return render_mako_context(request, '/appcc/constructrep/constructrep.html')


@login_exempt
def soft_package(request):
    """
    程序包17
    """
    return render_mako_context(request, '/appcc/constructrep/softpackage.html')


@login_exempt
def conf_package(request):
    """
    配置包18
    """
    return render_mako_context(request, '/appcc/constructrep/confpackage.html')


@login_exempt
def create_soft(request):
    """
    程序包17
    """
    return render_mako_context(request, '/appcc/constructrep/createsoftpackage.html')


@login_exempt
def package_info(request):
    """
    程序包17
    """
    return render_mako_context(request, '/appcc/constructrep/packageinfo.html')


@login_exempt
def create_conf(request):
    """
    配置包18
    """
    return render_mako_context(request, '/appcc/constructrep/createconfpackage.html')


@login_exempt
def jenkinsCI(request, app_name="1"):
    """
    JenkinsCI 19
    """
    """  server = jenkins.Jenkins('http://192.168.2.71:8080', username='guolei', password='6995508')
    jobs = server.get_jobs()
    json_str = json.dumps(jobs)
    app_dic = json.loads(json_str)
    app_list = []
    #for app in ['docker-test-crm', 'docker-test-kxcrm', 'docker-test-tms', 'docker-test-ga', 'docker-test-fss', 'docker-test-oms']:
    for app in app_dic:
        app = app.get('fullname')
        job_info = server.get_job_info(app)
        json_info = json.dumps(job_info)
        app_build_info = json.loads(json_info)
        print app_build_info.get('lastSuccessfulBuild')
        if app_build_info.get('lastSuccessfulBuild') == None:
            success_build_otherStyleTime = '1977-01-01 00:00:00'
        else:
            last_success = app_build_info.get('lastSuccessfulBuild').get('number')
            success_build_info = server.get_build_info(app, last_success)
            json_success_build_info_str = json.dumps(success_build_info)
            success_build_date = json.loads(json_success_build_info_str).get('timestamp')
            success_build_dateArray = time.localtime(success_build_date / 1000)
            success_build_otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", success_build_dateArray)

        if app_build_info.get('lastFailedBuild') == None:
            failed_build_otherStyleTime = '1977-01-01 00:00:00'
        else:
            last_failed =  app_build_info.get('lastFailedBuild').get('number')
            failed_build_info = server.get_build_info(app, last_failed)
            json_failed_build_info_str = json.dumps(failed_build_info)
            failed_build_info_date = json.loads(json_failed_build_info_str).get('timestamp')
            failed_build_dateArray = time.localtime(failed_build_info_date / 1000)
            failed_build_otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", failed_build_dateArray)

        if app_build_info.get('lastCompletedBuild') == None:
            complete_build_info_status = 'None'
            complete_build_info_user = 'None'
        else:
            last_complete = app_build_info.get('lastCompletedBuild').get('number')
            complete_build_info = server.get_build_info(app, last_complete)
            json_last_complete_info_str = json.dumps(complete_build_info)
            complete_build_info_status = json.loads(json_last_complete_info_str).get('result')
            complete_build_info_user = json.loads(json_last_complete_info_str).get('actions')[0].get('causes')[0].get(
                'userId')


        dict = {'name': app, 'success_build_date': success_build_otherStyleTime,
                'failed_build_info_date': failed_build_otherStyleTime,
                u'complete_build_info_status': complete_build_info_status,
                u'complete_build_info_user': complete_build_info_user, 'url': app_build_info.get('url')}
        #obj = models.Jenkins(app_name=app, last_success_time=success_build_otherStyleTime,
         #                    last_fail_time=failed_build_otherStyleTime, last_trigger_person=complete_build_info_user,
          #                   app_url=app_build_info.get('url'), last_status=complete_build_info_status)
        #obj.save()
        print dict
        #  'app_list': app_list,
        app_list.append(dict)"""
    print app_name
    app_list = Jenkins.objects.all()

    return render_mako_context(request, '/appcc/constructrep/jenkinsCI.html', {
        'app_list': app_list

    }
                               )

@login_exempt
def jenkins_app_build(request, app_name):
    """
    jenkins_app_build
    """
    """cconnect jenkins_server"""
    server = jenkins.Jenkins('http://192.168.2.71:8080', username='guolei', password='6995508')
    """检查项目是否在正在构建队列中"""
    builds = server.get_running_builds()
    json_info = json.dumps(builds)
    app_builds = json.loads(json_info)
    app_running_list = []
    """创建项目名称list"""
    for app_build in app_builds:
        app_running_list.append(app_build.get('name'))
    """当项目名不在app_running_list中时，构建项目"""
    if app_name not in app_running_list:
        next_build_number = server.get_job_info(app_name)['nextBuildNumber']
        server.build_job(app_name)
        """判断项目是否在构建队列中，当不在构建队列中时继续检查构建"""
        app_queue_status = True
        while app_queue_status == True:
            builds = server.get_running_builds()
            json_info = json.dumps(builds)
            app_builds = json.loads(json_info)
            app_running_list = []
            for app_build in app_builds:
                app_running_list.append(app_build.get('name'))
            if app_name in app_running_list:
                app_queue_status = False
        """判断项目是否构建完成"""
        app_build_status = True
        while app_build_status == True:
            app_build_info = server.get_build_info(app_name, next_build_number)
            json_info = json.dumps(app_build_info)
            app_build_info_json = json.loads(json_info)
            app_build_status = app_build_info_json.get('building')
        """将构建后的状态插入到数据库中"""
        app_build_person = app_build_info_json.get('actions')[0].get('causes')[0].get('userId')
        app_build_result = app_build_info_json.get('result')
        app_build_time = app_build_info_json.get('timestamp')
        app_builded_time = time.localtime(app_build_time / 1000)
        app_builded_date = time.strftime("%Y-%m-%d %H:%M:%S", app_builded_time)
        Jenkins.objects.filter(app_name=app_name).update(last_trigger_person=app_build_person)
        Jenkins.objects.filter(app_name=app_name).update(last_status=app_build_result)
        if app_build_result == 'SUCCESS':
            Jenkins.objects.filter(app_name=app_name).update(last_success_time=app_builded_date)
        else:
            Jenkins.objects.filter(app_name=app_name).update(last_fail_time=app_builded_date)
    return HttpResponse(json.dumps({"status": app_build_status}))


def jenkins_app_change_config(request):
    """
        jenkins_app_change_config
    :param request:
    :return:
    """
    """获取前段传递的参数"""
    app_name = request.GET['name']
    svn_url1 = request.GET['conf']
    """更改编码格式，解决中文字符问题"""
    reload(sys)
    sys.setdefaultencoding('utf-8')
    """替换前端传来的空格"""
    svn_url = svn_url1.replace('&nbsp;', ' ')
    """连接jenkins服务器"""
    server = jenkins.Jenkins('http://192.168.2.71:8080', username='guolei', password='6995508')
    """获取app_name配置，并将配置"""
    app_job_config = server.get_job_config(app_name)
    f = open(app_name + '.xml', 'w')
    f.write(app_job_config.encode('utf-8'))
    f.close()
    """处理xml文件，更改配置"""
    tree = ET.parse(app_name + '.xml')
    root = tree.getroot()
    for remote in root.iter('remote'):
        new_remote = svn_url
        remote.text = str(new_remote)
    tree.write(app_name + '.xml')
    """读取新配置文件"""
    conf = open(app_name + '.xml')
    all_the_conf = conf.read()
    """更改svn配置，并返回结果"""
    server.reconfig_job(app_name, all_the_conf)
    return HttpResponse(json.dumps({"status": request.GET['name']}))

def jenkins_app_stop(request, app_name):
    """
    jenkins_app_build
    """
    print app_name
    server = jenkins.Jenkins('http://192.168.2.71:8080', username='guolei', password='6995508')
    builds = server.get_running_builds()
    json_info = json.dumps(builds)
    app_builds = json.loads(json_info)
    print app_builds
    for app_build in app_builds:
        if app_build.get('name') == app_name:
            num = app_build.get('number')
            print num
            server.stop_build(app_name, num)
            Jenkins.objects.filter(app_name=app_name).update(last_status='ABORTED')

    return HttpResponse(json.dumps({"status": app_name}))

@login_exempt
def jenkins_publish_statistics(request):
    """
    jenkins_publish_statistics
    """
    return render_mako_context(request, '/appcc/constructrep/jenkins_publish_statistics.html')

@login_exempt
def jenkins_newitem(request):
    """
    jenkins_newitem
    """
    return render_mako_context(request, '/appcc/constructrep/jenkins_newitem.html')

@login_exempt
def jenkins_newjob(request):
    """
    新建Job 20
    """
    return render_mako_context(request, '/appcc/constructrep/jenkins_newjob.html')


@login_exempt
def authority_manage(request):
    """
    权限管理21
    """
    return render_mako_context(request, '/appcc/authoritymanage.html')


@login_exempt
def art_manage(request):
    """
    角色管理 22
    """
    return render_mako_context(request, '/appcc/artmanage.html')


@login_exempt
def API_manage(request):
    """
    API管理23
    """
    return render_mako_context(request, '/appcc/APImanage.html')


