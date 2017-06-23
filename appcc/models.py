# -*- coding: utf-8 -*-

from django.db import models,transaction
import json
import os
import datetime
import urllib
import requests
import jenkins
from common.log import logger
from blueking.component.shortcuts import get_client_by_request, get_client_by_user
from appcc.utils import safe_cast, index_of_list, get_client_by_bk_token
from django.conf import settings
from requests import exceptions as req_exceptions
from requests_toolbelt.utils import dump
from appcc.utils import random_name, md5_for_file
from django.core.files.storage import FileSystemStorage


class esbWrapper(object):
    """
    组件调用
    # 单纯的命名空间，和models分开
    """

    def __init__(self):
        pass

    def get_user_info(self, request):
        """
        获取qq
        """
        client = get_client_by_request(request)
        res = client.bk_login.get_user()
        if not res.get('result'):
            logger.error(u'get_user_info(Fail): %s' % res.get('message'))
            return None

        return res.get('data')

    def get_user_biz_list(self, request):
        """
        获取开平业务列表
        """
        client = get_client_by_request(request)
        biz_list = []
        res = client.cc.get_app_by_user()
        if not res.get('result'):
            logger.error(u'get_app_by_user_ext(Fail): %s' % res.get('message'))
            return []

        # 抽取业务列表
        for biz in res.get('data'):

            # 忽略系统默认创建的业务
            if safe_cast(biz.get('Default'), int):
                continue
            biz_list.append({'biz_id': biz.get('ApplicationID'), 'biz_name': biz.get('ApplicationName')})

        return biz_list

    def get_agent_status(self, request, ip_infos, company_id):
        '''
        查询agent状态，返回1为连线ok
        ip_infos = [{
            'ip': '10.104.217.163',
            'plat_id': 4
        }]
        '''
        client = get_client_by_request(request)
        res = client.gse.get_agent_status({
            'is_real_time': 1,
            'ip_infos': ip_infos
        })
        return res

    def get_plat_list(self, request):
        '''
        查询所有平台
        '''
        client = get_client_by_request(request)
        resp = client.cc.get_plat_id()
        data = {}
        if resp.get('result', False):
            plat_data = resp.get('data', [])
            for plat in plat_data:
                data.update({
                    '%s_%s' % (plat['platId'], ''): plat['platName']
                })
        return data

    def get_ip_by_biz_id(self, request, biz_id, company_id=''):
        '''
        获取用户指定业务下的主机列表
        '''
        client = get_client_by_request(request)

        ip_list = {
            'success': True,
            'data': []
        }
        ip_list_data, ip_infos = [], []
        resp = client.cc.get_app_host_list({'app_id': biz_id})

        # ugly api deal with
        if not resp['result'] and resp.get('message') != u'没有主机':
            logger.error(u"蓝鲸组件【cc.get_app_host_list】返回错误信息，查询出错：%s" % resp['message'])

        # ip去重
        s = []
        result = []
        for res in resp['data']:
            str = res['InnerIP'] + res['Source']
            if str not in s:
                result.append(res)
            s.append(str)

        resp['data'] = result

        # if resp['result']:
        ip_list['success'] = True
        data_info = resp['data']

        # 批量查询，生成接口参数
        for each in data_info:
            plat_id = safe_cast(each['Source'], int)

            # 云平台id腾讯云为1，gse存储为0，判断转换，其余不变
            ip_infos.append({
                "ip": each['InnerIP'],
                "plat_id": 0 if plat_id == 1 else plat_id,
            })

            # 初始化默认agent状态为异常
            source = '%s_%s' % (plat_id, '' if plat_id < 15 else company_id)
            ip_list['data'].append({
                "source": source,
                "alived": 0,
                "ipDesc": each['HostName'],
                "ip": each['InnerIP'],
                "outer_ip": each['OuterIP'],
                "os_name": each['OSName'],
                "host_id": each['HostID'],
            })

        # 查询agent状态列表
        ip_list_data = ip_list['data']
        gse_info = client.job.get_agent_status({'app_id': biz_id, 'ip_infos': ip_infos, 'is_real_time': 1})
        if gse_info['result']:
            gse_states = gse_info.get('data')
            for s in gse_states:
                index = index_of_list(ip_list_data, 'ip', s.get('ip'))
                if index != -1:
                    ip_list_data[index].update(alived=s.get('status'))
        else:
            logger.error(u"蓝鲸组件【gse.get_agent_status】返回错误信息，查询出错：%s" % gse_info['message'])

        return ip_list_data

    def get_email_group_list(self, request, biz_id=None):
        """
        获取邮件通知列表
        http://paas.bking.com/doc/index.html#api-API_BK_LOGIN-get_all_user
        """

        if biz_id is None:
            biz_id = request.user.profile.cur_biz_id
        client = get_client_by_request(request)

        # 查询业务信息
        app_info = client.cc.get_app_by_id({
            'app_id': biz_id,
        })
        app_info_data = app_info.get('data')[0]
        product_pm_list = app_info_data.get('ProductPm').split(';')
        maintiner_list = app_info_data.get('Maintainers').split(';')

        # 分组统计
        notify_list = [
            {
                'text': u"业务运维",
                'children': [
                    {
                        'text': u"所有业务运维",
                        'id': "Maintainers"
                    },
                ]
            },
            {
                'text': u"产品接口人",
                'children': [
                    {
                        'text': u"所有产品接口人",
                        'id': "ProductPm"
                    },
                ]
            }
        ]
        for pm in product_pm_list:
            # 产品类
            notify_list[1]['children'].append({
                'id': pm,
                'text': "%s" % pm,
            })
            # 运维类
        for maintiner in maintiner_list:
            notify_list[0]['children'].append({
                'id': maintiner,
                'text': "%s" % maintiner,
            })

        return notify_list

    def notify(self, bk_token, kwargs):
        """
        消息通知
        说明：消息通知功能需要企业用户自己实现，接口留空
        """
        # logger.info(u'notify: %s, %s' % (bk_token, kwargs))
        # client = get_client_by_bk_token(bk_token)
        #
        # notify_way = kwargs.get('notify_way')
        # try:
        #     if "sms" in notify_way:
        #         sms_kwargs = {
        #         }
        #         sms_result = client.cmsi.send_sms(sms_kwargs)
        #         logger.info('sms send complate:%s' % sms_result)
        #
        #     if "email" in notify_way:
        #         email_kwargs = {
        #         }
        #         email_result = client.cmsi.send_mail(email_kwargs)
        #         logger.info('email send complate:%s' % email_result)
        #
        #     if "weixin" in notify_way:
        #         weixin_kwargs = {
        #         }
        #         weixin_result = client.cmsi.send_qy_weixin(weixin_kwargs)
        #         logger.info('weixin send complate:%s' % weixin_result)
        # except Exception as e:
        #     logger.error(u'notify(Exception)： %s' % e)


    def execute_platform_task(self, bk_token, kwargs):
        '''
        启动平台作业
        '''

        task_inst_id = task_inst_name = ''
        try:
            logger.info(u'job.execute_platform_task->kwargs: %s' % kwargs)
            # client = get_client_by_bk_token(bk_token)
            ##########将执行job作业的用户改为
            client = get_client_by_user('admin')
            res = client.job.execute_platform_task(**kwargs)
            logger.info(u'job.execute_platform_task->res: %s' % res)
            if res.get('result', False):
                code, result = 0, True  # ijobs接口调用成功
                data = res.get('data', {})
                task_inst_id = data.get('taskInstanceId')
                task_inst_name = data.get('taskInstanceName')
                message = u'作业启动成功.'
            else:
                code, result = -1, False  # ijobs接口调用失败
                message = u'作业启动失败: %s' % res.get('message')
                logger.error(message)
        except Exception, e:
            code, result = -10000, False  # 接口调用异常
            message = u'作业启动异常: %s' % e
            logger.error(message)

        return {
            'result': result,
            'code': code,
            'task_inst_id': task_inst_id,
            'task_inst_name': task_inst_name,
            'message': message,
        }


class GitWrapper(object):
    """
    版本操作接口
    说明：review-todo 抽取try catch catch 结构为公共方法，紧急程度较低
    """

    def __init__(self):
        pass

    def create_update_config(self):
        """从db中读取api_host地址
            并对URL进行重新赋值
        """

        # 从db中读取api_host地址
        kv_info = Kv.objects.get_git_server_info(key='API_HOST')
        self.API_HOST = '%s%s%s%s' % ('http://', kv_info['ip'], ':', kv_info['port'])
        self.URL_UPLOAD = '%s/%s' % (self.API_HOST, 'api/uploadfile/')
        self.URL_RM = '%s/%s' % (self.API_HOST, 'api/deletefile/')
        self.URL_LS = '%s/%s' % (self.API_HOST, 'api/listfile/')
        self.URL_LS_COMMIT = '%s/%s' % (self.API_HOST, 'api/listnocommitfile/')
        self.URL_COMMIT = '%s/%s' % (self.API_HOST, 'api/commitfile/')
        self.URL_CHECKOUT = '%s/%s' % (self.API_HOST, 'api/checkoutfile/')
        self.URL_DIFF = '%s/%s' % (self.API_HOST, 'api/difftag/')

    def common_args(self, **extra):
        common_data = {
            'app_code': settings.APP_CODE,
            'app_secret': settings.SECRET_KEY,
        }
        common_data.update(extra)
        return common_data

    def debug(self, msg):
        if settings.DEBUG:
            print msg

    def data_process(self, data):
        """
        ls/status数据处理
        """
        new_data = sorted(data, key=lambda x: (not x['directory'], -x['lastModifyTime']))
        for f in new_data:
            f.update(lastModifyTime=datetime.datetime.fromtimestamp(
                int(f['lastModifyTime']) / 1000
            ).strftime('%Y-%m-%d %H:%M:%S'))
            if not settings.DEBUG:
                continue
            print '%s -- %s -- %s' % (
                f.get('fileName'),
                'd' if f.get('directory') else 'f',
                f.get('status'),
            )
        return new_data

    def res_diff_process(self, res):
        """
        diff 接口返回数据处理
        """
        data = res['data']
        add_modify_file = data['addFileList']
        add_modify_file.extend(data['modifyFileList'])

        return add_modify_file

    def res_process(self, res):
        """
        接口返回数据预处理
        """
        data = res['data'].get('data')
        new_data = self.data_process(data)
        return new_data

    def upload(self, request, app_id, project_id, need_extract, version_file, target_dir=None, timeout=30):
        """
        上传文件
        """
        self.create_update_config()
        self.debug('upload %s' % version_file.name)

        # 接口参数
        data = self.common_args(**{
            'appId': app_id,
            'projectId': project_id,
            'needUnzip': need_extract,
        })

        # 目标路径，不指定则采用根目录
        if target_dir:
            data.update(targetDir=target_dir)
        try:

            self.URL_UPLOAD = '%s/%s' % (self.API_HOST, 'api/uploadfile/')
            res = requests.post(self.URL_UPLOAD, data=data, files={'file': (version_file.name, version_file)},
                                timeout=timeout)
            res = res.json()
        except (req_exceptions.ConnectionError, req_exceptions.Timeout):

            # 访问备用接口服务器
            self.URL_UPLOAD = '%s/%s' % (self.API_HOST, 'api/uploadfile/')
            try:
                res = requests.post(self.URL_UPLOAD, data=data, files={'file': (version_file.name, version_file)},
                                    timeout=timeout)
                logger.info(u'版本服务器返回数据：%s' % res)
                res = res.json()
            except req_exceptions.Timeout:
                # HTTPConnectionPool(host=, port=8080): Read timed out. (read timeout=1)
                res = {'message': u'版本服务访问超时.', 'result': False}
            except req_exceptions.ConnectionError:
                res = {'message': u'版本服务器状态异常.', 'result': False}
        except ValueError as e:
            logger.error(u'upload(ValueError): %s' % e)
            res = {'message': u'版本服务器返回数据格式错误.', 'result': False}
        return res

    def ls(self, request, app_id, project_id, list_dir='/', timeout=10):
        """
        拉取文件列表
        """
        self.create_update_config()
        self.debug('ls / or %s' % list_dir)

        # 接口参数
        data = self.common_args(**{
            'appId': app_id,
            'projectId': project_id,
        })

        # 目标路径，不指定则采用根目录
        if list_dir:
            data.update(listDir=list_dir)
        try:
            res = requests.post(self.URL_LS, data=data, timeout=timeout)
            data = dump.dump_all(res)
            logger.info(u'版本服务器返回数据：%s' % data.decode('utf-8'))
            res = res.json()
            if res.get('result'):
                res['data'].update(data=self.res_process(res))
        except req_exceptions.Timeout:
            res = {'message': u'版本服务访问超时.', 'result': False}
        except req_exceptions.ConnectionError:
            res = {'message': u'版本服务器状态异常.', 'result': False}
        except ValueError as e:
            logger.error(u'ls(ValueError): %s' % e)
            res = {'message': u'版本服务器返回数据格式错误.', 'result': False}
        return res

    def rm(self, request, app_id, project_id, target_file, timeout=60):
        """
        删除文件
        """
        self.create_update_config()
        self.debug('rm %s' % target_file)

        # 接口参数
        data = self.common_args(**{
            'appId': app_id,
            'projectId': project_id,
            'targetFile': target_file,
        })
        try:
            res = requests.post(self.URL_RM, data=data, timeout=timeout)
            data = dump.dump_all(res)
            logger.info(u'版本服务器返回数据：%s' % data.decode('utf-8'))
            res = res.json()
        except req_exceptions.Timeout:
            res = {'message': u'版本服务访问超时.', 'result': False}
        except req_exceptions.ConnectionError:
            res = {'message': u'版本服务器状态异常.', 'result': False}
        except ValueError as e:
            logger.error(u'rm(ValueError): %s' % e)
            res = {'message': u'版本服务器返回数据格式错误.', 'result': False}
        return res

    def status(self, request, app_id, project_id, list_dir=None, timeout=60):
        """
        文件差异
        """
        self.create_update_config()
        self.debug('status / or %s' % list_dir)

        # 接口参数
        data = self.common_args(**{
            'appId': app_id,
            'projectId': project_id,
        })

        # 目标路径，不指定则采用根目录
        if list_dir:
            data.update(listDir=list_dir)
        try:
            res = requests.post(self.URL_LS_COMMIT, data=data, timeout=timeout)
            data = dump.dump_all(res)
            logger.info(u'版本服务器返回数据：%s' % data.decode('utf-8'))
            res = res.json()
            if res.get('result'):
                res['data'].update(data=self.res_process(res))
        except req_exceptions.Timeout:
            res = {'message': u'版本服务访问超时.', 'result': False}
        except req_exceptions.ConnectionError:
            res = {'message': u'版本服务器状态异常.', 'result': False}
        except ValueError as e:
            logger.error(u'status(ValueError): %s' % e)
            res = {'message': u'版本服务器返回数据格式错误.', 'result': False}

        return res

    def diff(self, auth_token, app_id, project_id, old_tag, new_tag, timeout=60):
        """
        对比文件差异
        """
        self.create_update_config()
        self.debug('status / or %s' % old_tag)
        # 接口参数

        data = self.common_args(**{
            "appId": app_id,
            "projectId": project_id,
            "oldTag": old_tag,
            "newTag": new_tag,
        })

        try:
            res = requests.post(self.URL_DIFF, data=data, timeout=timeout)
            data = dump.dump_all(res)
            logger.info(u'版本服务器返回数据：%s' % data.decode('utf-8'))
            res = res.json()
            if res.get('result'):

                # 生成合并的文件列表，包含变化和新增的文件
                res['data'].update(addModifyList=self.res_diff_process(res))
        except req_exceptions.Timeout:
            res = {'message': u'版本服务访问超时.', 'result': False}
        except req_exceptions.ConnectionError:
            res = {'message': u'版本服务器状态异常.', 'result': False}
        except ValueError as e:
            logger.error(u'ls(ValueError): %s' % e)
            res = {'message': u'版本服务器返回数据格式错误.', 'result': False}

        logger.info(u'diff: %s vs %s -> %s' % (old_tag, new_tag, res))
        return res

    def commit(self, request, app_id, project_id, tag, extra, timeout=60):
        """
        版本提交，生成tag
        extra {
            creator
            email
            remark
        }
        """
        self.create_update_config()
        self.debug('commit tag %s' % tag)

        # 接口参数
        data = self.common_args(**{
            'appId': app_id,
            'projectId': project_id,
            'tag': tag,
        })
        data.update(extra)
        try:
            res = requests.post(self.URL_COMMIT, data=data, timeout=timeout)
            data = dump.dump_all(res)
            logger.info(u'版本服务器返回数据：%s' % data.decode('utf-8'))
            res = res.json()
        except req_exceptions.Timeout:
            res = {'message': u'版本服务访问超时.', 'result': False}
        except req_exceptions.ConnectionError:
            res = {'message': u'版本服务器状态异常.', 'result': False}
        except ValueError as e:
            logger.error(u'commit(ValueError): %s' % e)
            res = {'message': u'版本服务器返回数据格式错误.', 'result': False}
        return res

    def checkout(self, request, app_id, project_id, tag, timeout=60):
        """
        迁出tag，覆盖目录
        """
        self.create_update_config()
        self.debug('checkout tag %s' % tag)

        # 接口参数
        data = self.common_args(**{
            'appId': app_id,
            'projectId': project_id,
            'tag': tag,
        })
        try:
            res = requests.post(self.URL_CHECKOUT, data=data, timeout=timeout)
            data = dump.dump_all(res)
            logger.info(u'版本服务器返回数据：%s' % data.decode('utf-8'))
            res = res.json()
        except req_exceptions.Timeout:
            res = {'message': u'版本服务访问超时.', 'result': False}
        except req_exceptions.ConnectionError:
            res = {'message': u'版本服务器状态异常.', 'result': False}
        except ValueError as e:
            logger.error(u'checkout(ValueError): %s' % e)
            res = {'message': u'版本服务器返回数据格式错误.', 'result': False}
        return res

# 封装频繁使用的api调用
esb = esbWrapper()
git = GitWrapper()

class KvManager(models.Manager):
    """
    table level method of Kv
    """

    def get_or_create_key(self, key, key_type, value=None):
        """
        获取key或者利用value创建key
        :param key_type: iV/fV/tV/cV
        """
        try:
            value = json.dumps(value) if key_type == 'tV' else value
        except:
            pass
        kv, _ = self.get_or_create(defaults={
            key_type: value
        }, **{
            'key': key
        })

        value = kv.__getattribute__(key_type)
        try:
            value = json.loads(value) if key_type == 'tV' else value
        except:
            pass
        return value

    def update_or_create_key(self, key, key_type, value=None):
        """
        获取key或者利用value更新key
        :param key_type: iV/fV/tV/cV
        """
        try:
            value = json.dumps(value) if key_type == 'tV' else value
        except:
            pass
        kv, _ = self.update_or_create(defaults={
            key_type: value
        }, **{
            'key': key
        })

        value = kv.__getattribute__(key_type)
        try:
            value = json.loads(value) if key_type == 'tV' else value
        except:
            pass
        return value

    def get_git_server_info(self, key=None):
        """
        获取GitServer中的信息
        """
        info = {
            'ip': '',
            'port': ''
        }
        try:
            kv = self.get(key=key)
            info['ip'] = kv.obj['ip']
            info['port'] = kv.obj['port']
        except Kv.DoesNotExist:
            logger.error(u"获取Kv信息失败")

        return info


class Kv(models.Model):
    """
    Kv配置表
    """
    key = models.CharField(u"键", max_length=255, db_index=True, primary_key=True)
    cV = models.CharField(u"字符值", max_length=255, null=True, blank=True)
    iV = models.IntegerField(u"整数值", null=True, blank=True)
    fV = models.FloatField(u"浮点值", null=True, blank=True)
    tV = models.TextField(u"文本值", null=True, blank=True)

    objects = KvManager()

    def __unicode__(self):
        return u'%s-%s-%s-%s-%s' % (self.key, self.cV, self.iV, self.fV, self.tV)

    class Meta:
        app_label = 'ci_master'
        verbose_name = u"系统配置表"
        verbose_name_plural = u"系统配置表"

    @property
    def obj(self):
        return json.loads(self.tV)

    @obj.setter
    def obj(self, data):
        self.tV = json.dumps(data)
        self.save()

class ApplicationInfoManage(models.Model):
    pass
class ApplicationInfo(models.Model):
    aid = models.CharField(u'应用ID', max_length=32, db_index=True, default='0001')
    appname = models.CharField(u'应用名称', max_length=45, unique=True)
    devleader = models.CharField(u'开发负责人', max_length=45)
    testleader = models.CharField(u'测试负责人', max_length=45)
    opsleader = models.CharField(u'运维负责人', max_length=45)
    lasttime = models.DateTimeField(u'最后访问时间')
    numcluster = models.IntegerField(u'集群数量',null=True)
    numhost = models.IntegerField(u'机器数量',null=True)
    numsoftpack = models.IntegerField(u'程序包数量',null=True)
    numconfpack = models.IntegerField(u'配置包数量',null=True)
    numinstance = models.IntegerField(u'实例数量',null=True)

    class Meta:
        verbose_name=u'应用'
        verbose_name_plural=u'应用'
    def applist(self):
        app_list=[]
        for app in self.objects.values('appname','devleader','testleader','opsleader','lasttime'):
            app_list.append({
                'appname':app.appname,
                'devleader':app.devleader,
                'testleader':app.testleader,
                'opsleaeder':app.opsleader,
                'lasttime':app.lasttime
            })
        return app_list

class VersionList(models.Model):
    """
    版本列表
    """
    vname = models.CharField(u'版本名', max_length=200)
    cversion = models.CharField(u'当前版本名', max_length=200,)
    pversion=models.CharField(u'前一版本名',max_length=200)
    iscversion=models.BinaryField(default=True)
    vpath = models.CharField(u'版本路径', max_length=200)
    ftype=models.CharField(u'文件类型',max_length=30)
    creator =models.CharField(u'创建者', max_length=45)


    class Meta:
        verbose_name = u'版本名'
        verbose_name_plural = u'版本名'

class Package(models.Model):
    name=models.CharField(u'包名称',max_length=45)
    type=models.IntegerField(u'包类型',choices=((0,u'程序包'),(1,u'配置包')))
    cId=models.IntegerField(u'包分类ID')
    source=models.CharField(u'包文件源',max_length=512)
    memo=models.CharField(u'备注',max_length=256,null=True)
    creator=models.CharField(u'包创建者',max_length=45)
    category=models.CharField(u'包分类标签',max_length=64)
    ctime=models.DateTimeField(u'创建时间')
    mtime=models.DateTimeField(u'最新更新时间')
    envfile=models.CharField(u'所属环境',max_length=45,choices=((0,u'dev'),(1,u'test'),(2,u'uat'),(3,u'pet'),(4,u'prod')))
    cversion=models.ForeignKey(VersionList)
    path=models.CharField(u'路径',max_length=200)
    class Meta:
        verbose_name=u'包名称'
        verbose_name_plural=u'包名称'

class HostInfoManage(models.Model):
    pass
class HostInfo(models.Model):
    pass
class EnvInfoManage(models.Model):
    pass
class EnvInfo(models.Model):

    pass

class VersionUploadManager(models.Manager):
    """
    文件操作接口
    """

    def add_file(self, project, version_file, need_extract, upload_ok):
        """
        添加一条记录
        """
        new_file = self.create(
            project=project,
            name=version_file.name,
            size=version_file.size,
            md5=md5_for_file(version_file.chunks()),
            need_extract=need_extract,
            upload_ok=upload_ok,
        )

        return new_file

class OverwriteStorage(FileSystemStorage):
    """
    本地存储相关，用于同名文件的覆盖处理
    """

    def get_available_name(self, name):

        # 如果文件名存在, 移除当前文件
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name




class VersionUploadFile(models.Model):
    """
    上传版本文件
    """
    app = models.ForeignKey('ApplicationInfo', help_text=u'关联应用')
    name = models.CharField(u"文件名", max_length=100)
    size = models.IntegerField(u"文件大小", default=0, blank=True, null=True)
    md5 = models.CharField(u"md5", max_length=32, blank=False, null=False)
    file = models.FileField(u"文件", upload_to='repo', storage=OverwriteStorage())
    uploaded_at = models.DateTimeField(u"上传时间", auto_now_add=True, db_index=True)
    upload_ok = models.BooleanField(u'是否上传成功', default=True)
    need_extract = models.BooleanField(u'是否需要解压', default=False)

    objects = VersionUploadManager()

    @property
    def url(self):
        return self.file.url

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-uploaded_at',)
        app_label = 'ci_master'
        verbose_name = u"上传版本文件"
        verbose_name_plural = u"上传版本文件"

class VersionInfoManager(models.Model):

    def init_version(self, request, app, version_name='v0.0.1'):
        """
        项目版本初始化
        """
        res = git.commit(request, app.biz_id, app.pk, version_name, {
            'creator': request.user.username, 'remark': 'first version init to v0.0.1', 'email': 'system'
        })
        version = self.create(version_name=version_name)
        return res, version

    def add_version(self, request, project, version_name, remark, email='system'):
        """
        提交并创建新版本
        """

        # 版本状态查询
        status = []
        res_status = git.status(request, project.biz_id, project.pk)
        if res_status.get('result'):
            status = res_status.get('data', {}).get('data', [])

        res = git.commit(request, project.biz_id, project.pk, version_name, {
            'creator': request.user.username, 'remark': remark, 'email': email
        })

        # 版本提交失败
        if not res.get('result'):
            return res, None

        version = self.create(version_name=version_name, commit_status=json.dumps(status))
        return res, version

class VersionInfo(models.Model):
    version_name = models.CharField(u'版本号', max_length=64)
    create_time = models.DateTimeField(u'版本创建时间', auto_now_add=True)
    commit_time = models.DateTimeField(u'最后一次版本提交时间', auto_now_add=True, db_index=True)
    commit_status = models.TextField(u'提交版本文件变更状态记录', default=json.dumps([]))

    objects = VersionInfoManager()

    def __unicode__(self):
        return u'%s-%s-%s' % (self.version_name, self.create_time, self.commit_time)

    class Meta:
        app_label = 'ci_master'
        verbose_name = u'版本信息'
        verbose_name_plural = u'版本信息'

    @property
    def status(self):
        return json.loads(self.commit_status)

    @status.setter
    def status(self, data):
        self.commit_status = json.dumps(data)
        self.save()

    def get_deleted_files(self):
        """
        获取最后一次提交时删除的文件列表
        """
        return [data['fileName'] for data in self.status if data.get('status') == 'deleted']


class JobManage(models.Model):
    pass
class Job(models.Model):
    pass
class ToolList(models.Model):
    """
    工具列表
    """
    tname=models.CharField(u'工具名称',max_length=45,null=False)
    tcataory=models.CharField(u'分类',max_length=45)
    creator=models.CharField(u'创建者',max_length=45)
    operator=models.CharField(u'可操作者',max_length=45)
    ctime=models.DateTimeField(u'创建时间',max_length=45)
    mtime=models.DateTimeField(u'更新时间',max_length=45)

    class Meta:
        verbose_name=u'工具名'
        verbose_name_plural=u'工具名'

    def toollist(cls, tool):
        return {
            'id': tool.pk,
            'tname': tool.tname,
            'tcataory': tool.tcataory,
            'creator': tool.creator,
            'operator': tool.operator,
            'ctime': tool.ctime,
            'mtime': tool.mtime,

        }

class FlowList(models.Model):
    """
    流程列表
    """
    fname = models.CharField(u'工具名称', max_length=45)
    fcataory = models.CharField(u'分类', max_length=45)
    creator = models.CharField(u'创建者', max_length=45)
    operator = models.CharField(u'可操作者', max_length=45)
    ctime = models.DateTimeField(u'创建时间', max_length=45)
    mtime = models.DateTimeField(u'更新时间', max_length=45)

    class Meta:
        verbose_name=u'流程名'
        verbose_name_plural=u'流程名'

class TaskTime(models.Model):
    """
    定时任务
    """
    ttname = models.CharField(u'工具名称', max_length=45)
    ttcataory = models.CharField(u'分类', max_length=45)
    creator = models.CharField(u'创建者', max_length=45)
    operator = models.CharField(u'可操作者', max_length=45)
    ctime = models.DateTimeField(u'创建时间', max_length=45)
    mtime = models.DateTimeField(u'更新时间', max_length=45)
    runstrateg=models.CharField(u'执行策略',max_length=200)
    state=models.CharField(u'运行状态',max_length=45,choices=(
        (0, u'未运行'), (1, u'运行中'), (2, u'异常'),
        (3, u'已停止'), ))

    class Meta:
        verbose_name=u'任务名'
        verbose_name_plural=u'任务名'

class Jenkins_url(models.Model):

    """jenkins_url"""
    app_name = models.CharField(u'项目名称', max_length=45)
    app_url = models.CharField(u'url', max_length=100)
    class Meta:
        verbose_name=u'jenkins_url'
        verbose_name_plural=u'jenkinsurl'

class Jenkins(models.Model):
    """jenkins model"""
    app_name = models.CharField(u'项目名称', max_length=45)
    last_success_time = models.DateTimeField(u'上次成功时间', max_length=45)
    last_fail_time = models.DateTimeField(u'上次失败时间', max_length=45)
    last_trigger_person = models.CharField(u'上次触发人员', max_length=45, null=True)
    app_url = models.CharField(u'url', max_length=100)
    last_status = models.CharField(u'上次构建状态', max_length=30)
    class Meta:
        verbose_name=u'jenkins'
        verbose_name_plural=u'jenkins'