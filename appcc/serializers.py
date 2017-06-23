# -*- coding: utf-8 -*-

from rest_framework import serializers
from appcc.models import ApplicationInfo,Package,VersionList

class ApplicationListSerializer(serializers.ModelSerializer):
    class Meta:
        model=ApplicationInfo
        fields=('appname','devleader','testleader','opsleader','lasttime','numcluster','numhost','numsoftpack','numconfpack')

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model=Package
        filelds=('name','type','cId','source','memo','creator','ctime','category','ctime','mtime','envfile','cversion','path')

class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model=VersionList
        fields=('vname','cversion','pversion','iscversion','vpath','ftype','creator')
