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

dirName = os.path.join(os.path.dirname(__file__),'uquality')
intentDirName = os.path.join(os.path.dirname(__file__),'uintent')


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

    matNames = data[1,:]
    nautilus25Data = data[3:6,:]
    nautilus4Data = data[7:12,:]
    nautilus8Data = data[13:17,:]
    minnowData = data[18:23,:]
    minnowM2Data = data[24:29,:]

    for i in range(1,len(nautilus25Data)):
        for j in range(1,len(nautilus25Data[0])):
            if nautilus25Data[i,j] == "enabled":
                qualFormat("hydra_research_nautilus",nautilus25Data[i,0],matNames[j],"B_250")



    for i in range(1,len(nautilus4Data)):
        for j in range(1,len(nautilus4Data[0])):
            if nautilus4Data[i,j] == "enabled":
                qualFormat("hydra_research_nautilus",nautilus4Data[i,0],matNames[j],"X_400")
                if nautilus4Data[0,j] == "enabled":
                    intentBuilder(matNames[j],nautilus4Data[i,0].lower())

    for i in range(1,len(nautilus8Data)):
        for j in range(1,len(nautilus8Data[0])):
            if nautilus8Data[i,j] == "enabled":
                qualFormat("hydra_research_nautilus",nautilus8Data[i,0],matNames[j],"X_800")

    for i in range(1,len(minnowData)):
        for j in range(1,len(minnowData[0])):
            if minnowData[i,j] == "enabled":
                qualFormat("hydra_research_minnow",minnowData[i,0],matNames[j],"0.4mm")
                if minnowData[0,j] == "enabled":
                    minnowIntentBuilder(matNames[j],minnowData[i,0].lower())

    for i in range(1,len(minnowM2Data)):
        for j in range(1,len(minnowM2Data[0])):
            if minnowM2Data[i,j] == "enabled":
                qualFormat("hydra_research_minnow_m2",minnowM2Data[i,0],matNames[j],"0.4mm")
                if minnowM2Data[0,j] == "enabled":
                    minnowM2IntentBuilder(matNames[j],minnowM2Data[i,0].lower())


def qualFormat(defName, type, matName, varName):
    weight = {"extra fine":"1","fine":"0","detail":"-1","normal":"-2","draft":"-3","extra draft":"-4"}
    printer = {"hydra_research_nautilus":"n","hydra_research_minnow":"m","hydra_research_minnow_m2":"mm2"}
    qualProf = "[general]\nversion = 4\nname = "+type+"\ndefinition = "+defName+"\n\n[metadata]\nsetting_version = 10\ntype = quality\nquality_type = "+type.lower()+"\nweight = "+weight[type.lower()]+"\nmaterial = "+matName+"\nvariant = "+varName+"\n\n[values]"
    filename = (dirName + "/hr" + printer[defName] + matName[2:] +"_"+ varName + "_" + type.lower() +".inst.cfg").replace(" ","_")
    with open(filename, 'w') as f:
        f.write(qualProf)
        f.close()

def intentBuilder(matName, qualType):
    print(qualType)
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
        print(filename)
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
qualBuilder('Universal Quality')
globalQualBuilder('UC Quality Global')
minnowGlobalQualBuilder('Minnow - Global')
minnowM2GlobalQualBuilder('Minnow M2 - Global')
