#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 27 14:15:41 2018

@author: Zach
"""

from __future__ import print_function
import os

from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
import tempfile
import shutil

import numpy as np
import requests

dirName = os.path.join(os.path.dirname(__file__),'quality')
intentDirName = os.path.join(os.path.dirname(__file__),'intent')


def directoryBuilder(dirName):
    if not os.path.exists(dirName):
        os.mkdir(dirName)
        print("Directory " , dirName ,  " Created ")
    else:
        print("Directory " , dirName ,  " already exists")
        shutil.rmtree(dirName)
        os.mkdir(dirName)

def downloader(FILENAME):
    SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
    store = file.Storage('storage.json')
    creds = store.get()
    path = os.path.dirname(__file__)

    if not creds or creds.invalid:
        secret = os.path.join(path,'client_secret.json')
        flow = client.flow_from_clientsecrets(secret, SCOPES)
        creds = tools.run_flow(flow, store)
    DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))

    SRC_MIMETYPE = 'application/vnd.google-apps.spreadsheet'
    DST_MIMETYPE = 'text/csv'
    with tempfile.TemporaryDirectory() as csvContainer:
        files = DRIVE.files().list(
            q='name="%s" and mimeType="%s"' % (FILENAME, SRC_MIMETYPE),
            orderBy='modifiedTime desc,name').execute().get('files', [])

        if files:
            fn = os.path.join(csvContainer,FILENAME+'.csv')
            print('Exporting "%s" as "%s"... ' % (files[0]['name'], fn), end='')
            data = DRIVE.files().export(fileId=files[0]['id'], mimeType=DST_MIMETYPE).execute()
            if data:
                with open(fn, 'wb') as f:
                    f.write(data)
                print('DONE')
            else:
                print('ERROR (could not download file)')
        else:
             print('!!! ERROR: File not found')
        dt = np.dtype(('U', 128))

        sheet = open(fn)



        data = np.genfromtxt(sheet, delimiter=",",dtype=dt)
    return data,dt

def qualBuilder(sheetName):
    matlist = []
    data,dt = downloader(sheetName)
    data1 = data

    enabledData = data[2,1:]
    intentData = data[3,1:]
    headers=data[[0,1],:]
    data = np.delete(data,(0,1,2,3),0) #delete rows

    skipPoint = np.where(enabledData == "no")[0]
    intentPoint = np.where(intentData == "yes")[0]

    titles=data[:,0]
    data = np.delete(data, 0,1) #delete columns

    r,c=np.shape(data)
    profs = np.zeros((r,c))
    profs = np.array(profs,dtype=dt)


    for i in range(r):
        for j in range(c):
            if j in skipPoint:
                continue
            if i in (0,4,5,12,13):
                profs[i,j]=titles[i]
            else:
                if len(data[i,j])!=0:
                    profs[i,j]=titles[i]+' = '+data[i,j]
                else:
                    profs[i,j]= ""


    for k in range(c):
        if k in skipPoint:
            continue
        varient=data[11,k]
        name = data[10,k]
        matName = name
        name = name[0:2]+'n'+name[2:]
        print('varient: '+varient)
        print('name: '+name)
        print('matname: '+matName)
        filename = (dirName + '/' + name + '_' + varient + '_' + data[8,k] +'.inst.cfg').replace(' ','_')
        np.savetxt(filename, profs[:,k], newline='\n',fmt='%s')
        if k in intentPoint:
            qualType = data[8,k].replace(' ','_')
            if '0.4' in sheetName:
                intentBuilder(matName, qualType)
    return

def minnowQualBuilder(sheetName):
    matlist = []
    data,dt = downloader(sheetName)
    data1 = data

    enabledData = data[2,1:]
    minnowIntentData = data[3,1:]
    headers=data[[0,1],:]
    data = np.delete(data,(0,1,2,3),0) #delete rows

    skipPoint = np.where(enabledData == "no")[0]
    intentPoint = np.where(minnowIntentData == "yes")[0]

    titles=data[:,0]
    data = np.delete(data, 0,1) #delete columns

    r,c=np.shape(data)
    profs = np.zeros((r,c))
    profs = np.array(profs,dtype=dt)


    for i in range(r):
        for j in range(c):
            if j in skipPoint:
                continue
            if i in (0,4,5,12,13):
                profs[i,j]=titles[i]
            else:
                if len(data[i,j])!=0:
                    profs[i,j]=titles[i]+' = '+data[i,j]
                else:
                    profs[i,j]= ""


    for k in range(c):
        if k in skipPoint:
            continue
        varient=data[11,k]
        name = data[10,k]
        matName = name
        name = name[0:2]+'m'+name[2:]
        filename = (dirName + '/' + name + '_' + varient + '_' + data[8,k] +'.inst.cfg').replace(' ','_')
        np.savetxt(filename, profs[:,k], newline='\n',fmt='%s')
        if k in intentPoint:
            qualType = data[8,k].replace(' ','_')
            if '0.4' in sheetName:
                minnowIntentBuilder(matName, qualType)
    return

def intentBuilder(matName, qualType):
    data = intentData
    dt = intentdt
    data = np.delete(data,(0,1),0)
    titles = data[:,0]
    np.delete(data,0,1)
    data = data[:,data[9]==qualType]

    r,c=np.shape(data)
    profs = np.zeros((r,c))
    profs = np.array(profs,dtype=dt)

    for i in range(r):
        for j in range(c):
            if i in (0,4,5,12,13):
                profs[i,j]=titles[i]
            else:
                if i == 10:
                    profs[i,j]=titles[i]+' = '+ matName
                elif len(data[i,j])!=0:
                    profs[i,j]=(titles[i]+' = '+data[i,j]).replace('@','=')
                else:
                    profs[i,j]= ""

    for k in range(c):
        varient=data[11,k]
        name = data[10,k]
        name = matName[0:2]+'n'+matName[2:]
        filename = (intentDirName + '/' + name + '_' + varient + '_' + qualType + '_' + data[8,k] +'.inst.cfg').replace(' ','_')
        np.savetxt(filename, profs[:,k], newline='\n',fmt='%s')

def minnowIntentBuilder(matName, qualType):
    data = minnowIntentData
    dt = minnowIntentdt
    data = np.delete(data,(0,1),0)
    titles = data[:,0]
    np.delete(data,0,1)
    data = data[:,data[9]==qualType]

    r,c=np.shape(data)
    profs = np.zeros((r,c))
    profs = np.array(profs,dtype=dt)

    for i in range(r):
        for j in range(c):
            if i in (0,4,5,12,13):
                profs[i,j]=titles[i]
            else:
                if i == 10:
                    profs[i,j]=titles[i]+' = '+ matName
                elif len(data[i,j])!=0:
                    profs[i,j]=(titles[i]+' = '+data[i,j]).replace('@','=')
                else:
                    profs[i,j]= ""

    for k in range(c):
        varient=data[11,k]
        name = data[10,k]
        name = matName[0:2]+'m'+matName[2:]
        filename = (intentDirName + '/' + name + '_' + varient + '_' + qualType + '_' + data[8,k] +'.inst.cfg').replace(' ','_')
        np.savetxt(filename, profs[:,k], newline='\n',fmt='%s')

def globalQualBuilder(sheetName):
    data,dt = downloader(sheetName)
    data1 = data

    headers=data[[0,1],:]
    data = np.delete(data,(0,1),0) #delete rows


    titles=data[:,0]
    data = np.delete(data, 0,1) #delete columns

    r,c=np.shape(data)
    profs = np.zeros((r,c))
    profs = np.array(profs,dtype=dt)


    for i in range(r):
        for j in range(c):
            if i in (0,4,5,12):
                profs[i,j]=titles[i]
                #print('count',profs[i,j])
            else:
                if len(data[i,j])!=0:
                    profs[i,j]=titles[i]+' = '+data[i,j]
                    #print('not count',profs[i,j])
                else:
                    profs[i,j]= ""

    for k in range(c):
        varient=data[11,k]
        name = data[10,k]
        name = name[0:2]+'n'+name[2:]
        varient=varient.replace(' ','_')
        filename = dirName + '/hrn_global_' + data[8,k]+'_quality.inst.cfg'
        np.savetxt(filename, profs[:,k], newline='\n',fmt='%s')
    return

def minnowGlobalQualBuilder(sheetName):
    data,dt = downloader(sheetName)
    data1 = data

    headers=data[[0,1],:]
    data = np.delete(data,(0,1),0) #delete rows


    titles=data[:,0]
    data = np.delete(data, 0,1) #delete columns

    r,c=np.shape(data)
    profs = np.zeros((r,c))
    profs = np.array(profs,dtype=dt)


    for i in range(r):
        for j in range(c):
            if i in (0,4,5,12):
                profs[i,j]=titles[i]
                #print('count',profs[i,j])
            else:
                if len(data[i,j])!=0:
                    profs[i,j]=titles[i]+' = '+data[i,j]
                    #print('not count',profs[i,j])
                else:
                    profs[i,j]= ""

    for k in range(c):
        varient=data[11,k]
        name = data[10,k]
        name = name[0:2]+'n'+name[2:]
        varient=varient.replace(' ','_')
        filename = dirName + '/hrm_global_' + data[8,k]+'_quality.inst.cfg'
        np.savetxt(filename, profs[:,k], newline='\n',fmt='%s')
    return

def minnowM2QualBuilder(sheetName):
    matlist = []
    data,dt = downloader(sheetName)
    data1 = data

    enabledData = data[2,1:]
    minnowM2IntentData = data[3,1:]
    headers=data[[0,1],:]
    data = np.delete(data,(0,1,2,3),0) #delete rows

    skipPoint = np.where(enabledData == "no")[0]
    intentPoint = np.where(minnowM2IntentData == "yes")[0]

    titles=data[:,0]
    data = np.delete(data, 0,1) #delete columns

    r,c=np.shape(data)
    profs = np.zeros((r,c))
    profs = np.array(profs,dtype=dt)


    for i in range(r):
        for j in range(c):
            if j in skipPoint:
                continue
            if i in (0,4,5,12,13):
                profs[i,j]=titles[i]
            else:
                if len(data[i,j])!=0:
                    profs[i,j]=titles[i]+' = '+data[i,j]
                else:
                    profs[i,j]= ""


    for k in range(c):
        if k in skipPoint:
            continue
        varient=data[11,k]
        name = data[10,k]
        matName = name
        name = name[0:2]+'mm2'+name[2:]
        filename = (dirName + '/' + name + '_' + varient + '_' + data[8,k] +'.inst.cfg').replace(' ','_')
        np.savetxt(filename, profs[:,k], newline='\n',fmt='%s')
        if k in intentPoint:
            qualType = data[8,k].replace(' ','_')
            if '0.4' in sheetName:
                minnowM2IntentBuilder(matName, qualType)
    return

def minnowM2IntentBuilder(matName, qualType):
    data = minnowM2IntentData
    dt = minnowM2Intentdt
    data = np.delete(data,(0,1),0)
    titles = data[:,0]
    np.delete(data,0,1)
    data = data[:,data[9]==qualType]

    r,c=np.shape(data)
    profs = np.zeros((r,c))
    profs = np.array(profs,dtype=dt)

    for i in range(r):
        for j in range(c):
            if i in (0,4,5,12,13):
                profs[i,j]=titles[i]
            else:
                if i == 10:
                    profs[i,j]=titles[i]+' = '+ matName
                elif len(data[i,j])!=0:
                    profs[i,j]=(titles[i]+' = '+data[i,j]).replace('@','=')
                else:
                    profs[i,j]= ""

    for k in range(c):
        varient=data[11,k]
        name = data[10,k]
        name = matName[0:2]+'mm2'+matName[2:]
        filename = (intentDirName + '/' + name + '_' + varient + '_' + qualType + '_' + data[8,k] +'.inst.cfg').replace(' ','_')
        np.savetxt(filename, profs[:,k], newline='\n',fmt='%s')

def minnowM2GlobalQualBuilder(sheetName):
    data,dt = downloader(sheetName)
    data1 = data

    headers=data[[0,1],:]
    data = np.delete(data,(0,1),0) #delete rows


    titles=data[:,0]
    data = np.delete(data, 0,1) #delete columns

    r,c=np.shape(data)
    profs = np.zeros((r,c))
    profs = np.array(profs,dtype=dt)


    for i in range(r):
        for j in range(c):
            if i in (0,4,5,12):
                profs[i,j]=titles[i]
                #print('count',profs[i,j])
            else:
                if len(data[i,j])!=0:
                    profs[i,j]=titles[i]+' = '+data[i,j]
                    #print('not count',profs[i,j])
                else:
                    profs[i,j]= ""

    for k in range(c):
        varient=data[11,k]
        name = data[10,k]
        name = name[0:2]+'n'+name[2:]
        varient=varient.replace(' ','_')
        filename = dirName + '/hrmm2_global_' + data[8,k]+'_quality.inst.cfg'
        np.savetxt(filename, profs[:,k], newline='\n',fmt='%s')
    return

directoryBuilder(dirName)
directoryBuilder(intentDirName)
intentData, intentdt = downloader('UC Quality Intent')
minnowIntentData, minnowIntentdt = downloader('Minnow - Intent')
minnowM2IntentData, minnowM2Intentdt = downloader('Minnow M2 - Intent')
qualBuilder('UC Quality B 0.25')
qualBuilder('UC Quality X 0.40')
qualBuilder('UC Quality X 0.80')
minnowQualBuilder('Minnow - Quality - 0.40mm')
minnowM2QualBuilder('Minnow M2 - Quality - 0.40mm')
globalQualBuilder('UC Quality Global')
minnowGlobalQualBuilder('Minnow - Global')
minnowM2GlobalQualBuilder('Minnow M2 - Global')
