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

dirName = os.path.join(os.path.dirname(__file__),'..','Profiles','nautilusquals')

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
            if i in (0,4,5,12,13):
                profs[i,j]=titles[i]
            else:
                if len(data[i,j])!=0:
                    profs[i,j]=titles[i]+' = '+data[i,j]
                else:
                    profs[i,j]= ""

    for k in range(c):
        varient=data[11,k]
        name = data[10,k]
        name = name[0:2]+'n'+name[2:]
        varient=varient.replace(' ','_')
        filename = dirName + '/' + name + '_' + varient + '_' + data[8,k]+'.inst.cfg'
        print(filename)
        np.savetxt(filename, profs[:,k], newline='\n',fmt='%s')
    return

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

qualBuilder('UC Quality B 0.25')
qualBuilder('UC Quality X 0.40')
qualBuilder('UC Quality X 0.80')
globalQualBuilder('UC Quality Global')
