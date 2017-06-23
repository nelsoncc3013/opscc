# -*- coding: utf-8 -*-

from appcc.models import ApplicationInfo
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from serializers import ApplicationListSerializer,PackageSerializer,VersionSerializer
from common.mymako import render_mako_context
from django.shortcuts import render, render_to_response, get_object_or_404
from models import ApplicationInfo,Package,VersionList

class JSONResponse(HttpResponse):
    """
    用于返回Json类型
    """
    def __init__(self,data,**kwargs):
        content=JSONRenderer().render(data)
        kwargs['content_type']='application/json'
        super(JSONResponse,self).__init__(content,**kwargs)

@csrf_exempt
def applition_list(request):
    if request.method == 'GET':
        application = ApplicationInfo.objects.all()
        serializer = ApplicationListSerializer(application, many=True)
        return JSONResponse(serializer.data)
    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = ApplicationListSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data, status=201)
        return JSONResponse(serializer.errors, status=400)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = ApplicationInfo.objects.all()
    serializer_class = ApplicationListSerializer


class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer


class VersionViewSet(viewsets.ModelViewSet):
    queryset = VersionList.objects.all()
    serializer_class = VersionSerializer