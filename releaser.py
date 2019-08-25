import os
import tempfile
from distutils.dir_util import copy_tree
import zipfile
import shutil
import glob
import itertools as it

def fileList(fileName,reldir):
    files = list()
    for (dirpath, dirnames, filenames) in os.walk(fileName):
        files += [os.path.join(os.path.relpath(dirpath,reldir), file) for file in filenames]
    return files

exclude = ['xtcf20','pacf','htpla','.ini','Icon','Store']
path = os.path.dirname(os.path.realpath(__file__))
#print(path)
folder = os.path.join(path,'Profiles')
configFiles = fileList(os.path.join(path,"Profiles"),folder)


for cf in configFiles:
    for ex in exclude:
        if ex in cf:
            configFiles.remove(cf)

configFiles.remove('nautilusvars\desktop.ini')

with zipfile.ZipFile('Nautilus.zip', 'w') as zf:
    # add everything relevant
    for item in configFiles:
        if not os.path.isdir(item):
            zf.write(os.path.join(folder,item),item)
zf.close()
print("Update version numbers before release!")
