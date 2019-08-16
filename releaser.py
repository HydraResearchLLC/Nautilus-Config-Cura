import os
import tempfile
from distutils.dir_util import copy_tree
import zipfile
import shutil
import glob

def fileList(fileName):
    files = list()
    print('arrived')
    for (dirpath, dirnames, filenames) in os.walk(fileName):
        files += [os.path.join(dirpath, file) for file in filenames]
    return files

def getListOfFiles(dirName):
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory

        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            print(entry)
            allFiles.append(fullPath)

    return allFiles

path = os.path.dirname(os.path.realpath(__file__))
#print(path)
configFiles = fileList(os.path.join(path,"Profiles"))
folder = os.path.join(path,'Profiles')
#print(folder)
print(len(configFiles))


"""
for item in configFiles:
    if 'Icon' in os.path.relpath(item):
        print("Got it: ")
        print(item)
    else:
        print("Normal file: ")
        print(item)


    # zip the file as a .curapackage so it's ready to go
with zipfile.ZipFile(os.path.join('Nautilus.zip'), 'w') as zf:
    # add everything relevant
    for item in configFiles:
        print(item)
        zf.write(item)
zf.close()
print("Update version numbers before release!")
"""
