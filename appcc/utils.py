# -*- coding: utf-8 -*-
import os
import re
import hashlib
import random
import string
import tarfile
from itertools import groupby
from operator import itemgetter

from django.conf import settings
from django.core.exceptions import ValidationError

from blueking.component.shortcuts import ComponentClient
from common.log import logger


def is_chinese(char):
    """判断是否包含中文"""
    if not isinstance(char, unicode):
        char = char.decode('utf8')
    if re.search(ur"[\u4e00-\u9fa5]+", char):
        return True
    else:
        return False


def is_space(char):
    """判断是否包含空格"""
    if re.search(ur"\s", char):
        return True
    else:

        return False


def random_name(prefix=None, suffix=None, default_length=10):
    """
    生成随机字符串
    """
    name = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(default_length))

    # 前后缀
    if prefix:
        name = '%s-%s' % (prefix, name)
    if suffix:
        name = '%s-%s' % (name, suffix)

    return name


def deep_getattr(obj, attr):
    '''
    Recurses through an attribute chain to get the ultimate value.
    http://pingfive.typepad.com/blog/2010/04/deep-getattr-python-function.html
    '''
    return reduce(getattr, attr.split('.'), obj)


def index_of_list(objarr, key, val):
    """
    根据对象的某一属性寻找对象在其所在列表中的位置
    """
    return next((k for k, v in enumerate(objarr) if v[key] == val), -1)


def group_by(item_list, key_or_index_tuple, dict_result=False, aggregate=None, as_key=None):
    '''
    对列表中的字典元素进行groupby操作，依据为可排序的某个key
    :param item_list: 待分组字典列表或元组列表
    :param key_or_index_tuple: 分组关键字或位置列表
    :param dict_result: 是否返回字典格式
    :return: 可迭代的groupby对象或者字典
    http://stackoverflow.com/questions/21674331/group-by-multiple-keys-and-summarize-average-values-of-a-list-of-dictionaries
    '''

    list_sorted = sorted(item_list, key=itemgetter(*key_or_index_tuple))
    group_result = groupby(list_sorted, key=itemgetter(*key_or_index_tuple))
    if dict_result:
        return {k: list(g) for k, g in group_result}
    else:
        return group_result


def safe_cast(val, to_type, default=None):
    '''
    安全类型转换
    '''
    try:
        return to_type(val)
    except ValueError:
        return default or val
    except TypeError:
        return default or val


def size_mapper(size):
    """
    1G/1M/1K/1 --> 1024*1024*1024/1024*1024/1024/1Byte
    """

    if isinstance(size, int):
        return size
    else:
        size = size.lower()

    if size.endswith('g'):
        factor = 1024 * 1024 * 1024.0
    elif size.endswith('m'):
        factor = 1024 * 1024.0
    elif size.endswith('k'):
        factor = 1024.0
    else:
        raise ValidationError(u'格式错误，仅支持【G/M/K】结尾的大小标记字符串.')
    size = size.replace('g', '').replace('m', '').replace('k', '')
    return int(size) * factor


def md5_for_file(chunks):
    """
    计算文件的md5
    """
    md5 = hashlib.md5()
    for data in chunks:
        md5.update(data)
    return md5.hexdigest()


def unpack_archive(file_path):
    """
    压缩包解压
    """

    tar = None
    try:
        tar = tarfile.open(file_path)
        tar.extractall(path=os.path.dirname(file_path))
    except Exception as e:
        logger.error('unpack_archive:(Exception): %s' % e)
    finally:
        if tar is not None:
            tar.close()


def parse_path(path):
    """
    目录解析 move to utils later
    """
    # 目录规范化
    if not path.startswith('/'):
        path = '/%s' % path
    if not path.endswith('/'):
        path = '%s/' % path

    # 目录结构解析
    if path == '/':
        parent_dir = None
        path_list = []
    else:
        _path_list = path.split('/')[1:-1]
        path_list = []
        for i in xrange(len(_path_list)):
            _path = '/%s' % '/'.join(_path_list[:i + 1])
            path_list.append({'name': _path_list[i], 'path': _path})

        # 特殊处理
        parent_dir = os.path.dirname(os.path.dirname(path))
    return path, path_list, parent_dir


def get_client_by_bk_token(auth_token):
    '''
    直接用auth_token组装common_args并生成client
    '''
    return ComponentClient(settings.APP_ID, settings.APP_TOKEN, common_args={'bk_token': auth_token})


def get_client_by_common_args(common_args):
    '''
    直接用common_args组装client
    '''
    return ComponentClient(settings.APP_ID, settings.APP_TOKEN, common_args=common_args)
