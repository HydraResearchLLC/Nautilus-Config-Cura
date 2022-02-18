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
import xml.etree.ElementTree as ET
import tempfile
import xmltodict
import json

import numpy as np
import requests

def indent(elem, level=0):
  i = "\n" + level*"  "
  if len(elem):
    if not elem.text or not elem.text.strip():
      elem.text = i + "  "
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
    for elem in elem:
      indent(elem, level+1)
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
  else:
    if level and (not elem.tail or not elem.tail.strip()):
      elem.tail = i

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
    DST_MIMETYPE = 'text/tab-separated-values'
    with tempfile.TemporaryDirectory() as tsvContainer:
        files = DRIVE.files().list(
            q='name="%s" and mimeType="%s"' % (FILENAME, SRC_MIMETYPE),
            orderBy='modifiedTime desc,name').execute().get('files', [])

        if files:
            fn = os.path.join(tsvContainer,'NautilusMat.tsv')
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


        dirName = os.path.join(path,'materials')
        if not os.path.exists(dirName):
            os.mkdir(dirName)
            print("Directory " , dirName ,  " Created ")
        else:
            print("Directory " , dirName ,  " already exists")

        sheet = open(fn)
        sheetData = np.genfromtxt(sheet, delimiter = '\t', dtype=np.dtype(('U', 512)),filling_values=1)
        enabledData = sheetData[1,1:]
        excTitleData = []
        for i in range(1,len(sheetData[1])):
            excTitleData.append(('hr_'+sheetData[2,i]+'_'+sheetData[3,i]+'.xml.fdm_material').lower())
        #excData = np.vstack((np.array(excTitleData),sheetData[53,1:],sheetData[75,1:],sheetData[84,1:])) #make sure these are the lines where the hardware compatible for 0.4mm nozzle is for each printer
        skipPoint = np.where(enabledData == "no")[0]
        sheetData = np.delete(sheetData, (0,1), axis=0)
        catTitles = sheetData[:,0]
        matcostdata = '{'
        #exclusionCrafter(excData)
        for i in range(1,len(sheetData[1])):
            if i-1 in skipPoint:
                #print(i)
                continue
            else:
                catData = [s.replace('@',' ') for s in sheetData[:,i]]
                GUIDdata = catData[5]
                Costdata = catData[13]
                Weightdata = catData[14]
                matcostdata+='\"'+GUIDdata+'\": {\"spool_weight\": '+Weightdata+', \"spool_cost\": '+Costdata+'},'
                xmlCrafter(catTitles,catData,dirName)
        matcostdata = matcostdata[:-1]+'}'
        myfile = open(os.path.join(path,'matCosts.txt'),'w')
        myfile.write(matcostdata)

    return

def xmlCrafter(titles,data,directory):
    fdmmaterial = ET.Element('fdmmaterial')
    metadata = ET.SubElement(fdmmaterial, 'metadata')
    name = ET.SubElement(metadata, 'name')
    properties = ET.SubElement(fdmmaterial, 'properties')
    settings = ET.SubElement(fdmmaterial,'settings')
    machine = ET.SubElement(settings,'machine')
    machine2 = ET.SubElement(settings,'machine')
    headers = [name, metadata, properties, settings, machine, machine2]
    i=k=0
    colonSignal = list(titles).index("material_flow")

    for j in range(len(titles)):
        print(titles[j]+' for k ='+str(k))
        if titles[j] == '':
            k+=1
            i = 0
            if k==1 or k == 3:
                i+=1
            continue
        if titles[j][0]=='-':
            print('hyphen')
            if 'nautilus' in titles[j]:
                machine_identifier = ET.SubElement(machine, 'machine_identifier', manufacturer='Hydra Research', product='Hydra Research Nautilus')
                mac = machine
            elif 'm2' in titles[j]:
                machine_identifier = ET.SubElement(machine, 'machine_identifier', manufacturer='Hydra Research', product='Hydra Research Minnow M2')
                mac = machine
            elif 'minnow' in titles[j]:
                machine_identifier1 = ET.SubElement(machine2, 'machine_identifier', manufacturer='Hydra Research', product='Hydra Research Minnow')
                mac = machine2
        if data[j] == '':
            continue
        elif k < 3:
            headers[k].append(ET.Element(titles[j]))
            headers[k][i].text = data[j]
            i += 1
        elif k == 3:
            if j < colonSignal:
                headers[k].append(ET.Element('setting', key = titles[j]))
            else:
                headers[k].append(ET.Element('cura:setting', key = titles[j]))
            headers[k][i+1].text = data[j]
            #print('setting: '+str(titles[j])+' to: '+str(data[j]))
            #print(k)
            i+=1
        elif k > 3:
            if 'hot' in titles[j]:
                l = 0
                hotend = ET.SubElement(mac, titles[j], id = data[j])
            elif '_' in titles[j]:
                hotend.append(ET.Element('cura:setting', key = titles[j]))
                hotend[l].text = data[j]
                l+=1
            else:
                hotend.append(ET.Element('setting', key = titles[j]))
                hotend[l].text = data[j]
                l+=1

    titlename = os.path.join(directory,'hr_'+data[0]+'_'+data[3]+'.xml.fdm_material').replace(' ','_').lower().replace('-','')
    indent(fdmmaterial)
    mydata = ET.tostring(fdmmaterial,encoding="unicode",method='xml')
    mydata = mydata.replace('<fdmmaterial>', '<?xml version="1.0" encoding="UTF-8"?>\n<fdmmaterial xmlns="http://www.ultimaker.com/material" version="1.3" xmlns:cura="http://www.ultimaker.com/cura">').replace('<color_code>','<color_code>#')
    myfile = open(titlename,'w')
    myfile.write(mydata)
    return

def exclusionCrafter(data):
    nautilusExclusion = []
    minnowExclusion = []
    minnowM2Exclusion = []
    path = os.path.dirname(__file__)

    i=0
    j=0
    k=0
    while i < len(data[0,:]):
        if 'no' in data[1,i]:
            nautilusExclusion.append(data[0,i])
        i += 1

    while j < len(data[0,:]):
        if 'no' in data[2,j]:
            minnowExclusion.append(data[0,j])
        j += 1

    while k < len(data[0,:]):
        if 'no' in data[3,k]:
            minnowM2Exclusion.append(data[0,k])
        k += 1

    folder = os.path.join(path,'exclusion')
    if not os.path.exists(folder):
        os.mkdir(folder)
        print("Directory " , folder ,  " Created ")
    else:
        print("Directory " , folder ,  " already exists")

    with open('hydra_research_excluded_materials.json','r') as f:
        doc = f.read()
        obj = json.loads(doc)


        obj['metadata']['exclude_materials'] = str(nautilusExclusion)

        with open(os.path.join(folder,'hydra_research_nautilus_excluded_materials.def.json'),'w') as g:
            g.write(json.dumps(obj,indent=4))
            g.close()

        obj['metadata']['exclude_materials'] = str(minnowExclusion)

        with open(os.path.join(folder,'hydra_research_minnow_excluded_materials.def.json'),'w') as g:
            g.write(json.dumps(obj,indent=4))
            g.close()

        obj['metadata']['exclude_materials'] = str(minnowM2Exclusion)

        with open(os.path.join(folder,'hydra_research_minnow_m2_excluded_materials.def.json'),'w') as g:
            g.write(json.dumps(obj,indent=4))
            g.close()
        f.close()

downloader('Hydra Research Materials')
#downloader('Test Material')
