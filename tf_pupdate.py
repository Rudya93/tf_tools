import configparser
import requests
import platform
import os
import sys
import shutil
from pathlib import Path
from lxml import html
import urllib.request
import zipfile
import sys
import re
import getopt

tfver = 0.8
debug = False
verbose = False

p_os      = sys.platform
p_arch   = platform.architecture()[0]

if p_arch == '64bit':
  p_tfarch = 'amd64'
else:
  p_tfarch = '386'

def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]

print("Terraform main and provider update tool - version:",tfver,"- Arnvid L. Karstad / Basefarm")
print("Running updates for",p_os,p_arch,"/",p_tfarch)

if sys.version_info<(3,6,0):
  sys.stderr.write("You need python 3.6 or later to run this script\n")
  exit(1)

fullCmdArguments = sys.argv
argumentList = fullCmdArguments[1:]

unixOptions = "hdv"
gnuOptions = ["help","debug","verbose"]
try:
    arguments, values = getopt.getopt(argumentList, unixOptions, gnuOptions)
except getopt.error as err:
    print (str(err))
    sys.exit(2)

for currentArgument, currentValue in arguments:
    if currentArgument in ("-v", "--verbose"):
        print ("enabling verbose mode.")
        verbose = True
    elif currentArgument in ("-h", "--help"):
        print ("displaying help")
        print ("-h or --help - this text")
        print ("-d or --debug - enable debug mode")
        print ("-v or --verbose - enable verbose mode")
        exit(1)
    elif currentArgument in ("-d", "--debug"):
        print ("enabling debug mode.")
        debug = True

config = configparser.ConfigParser()
config.read('tf_pupdate.ini')
config.sections()

tmp_dir =  os.path.expanduser(config['PATHS'].get('tmp_dir'))
plugins_dir = os.path.expanduser(config['PATHS'].get('plugins_dir'))
plugins_dir = plugins_dir+"/"+p_os+"_"+p_tfarch

tf_dir = config['PATHS'].get('tf_dir')

if debug : print(tmp_dir)
if debug : print(plugins_dir)

if not (os.path.isdir(tmp_dir)) :
  if (os.path.exists(tmp_dir)):
    print("error: path for tmp_dir exists but is not a folder")
    exit(1)
  else:
    print("error: path for tmp_dir does not exist - creating.")
    os.makedirs(tmp_dir, exist_ok=True)

if not (os.path.isdir(plugins_dir)) :
  if (os.path.exists(plugins_dir)):
    print("error: path for plugins_dir exists but is not a folder")
    exit(1)
  else:
    print("error: path for plugins_dir does not exist - creating.")
    os.makedirs(plugins_dir, exist_ok=True)

print("Checking tf_gupdate.ini for list of activated providers:")

#for section in config.sections():
#  print("Section: %s" % section)
release_url = config['URLS'].get('release_url')
for option in config.options('PROVIDERS'):
  if config['PROVIDERS'].getboolean(option):
    if verbose : print("Provider:",option,"enabled - checking versions")
    provider_url = release_url+option+"/"
    if debug : print("Grabbing list from:",provider_url)
    webcontent = requests.get(provider_url)
    html_content = html.fromstring(webcontent.content)
    nodes = html_content.xpath('/html/body/ul/li/a/text()')
    tfp_filename=nodes[1]
    tfp_version=remove_prefix(tfp_filename, option+"_")
    tfp_lfilename=option+"_v"+tfp_version
    tfp_lfilename_x4=option+"_v"+tfp_version+"_x4"
    tfp_lfilename_x5=option+"_v"+tfp_version+"_x5"
    tfp_url = provider_url+tfp_version+"/"+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip"
    tfp_lzippath = tmp_dir+"/"+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip"
    if debug : print(tfp_url)
    if debug : print(tfp_lfilename)
    tfp_lfile = Path(plugins_dir+"/"+tfp_lfilename)
    tfp_lfile_x4 = Path(plugins_dir+"/"+tfp_lfilename_x4)
    tfp_lfile_x5 = Path(plugins_dir+"/"+tfp_lfilename_x5) 
    if debug : print("looking for ",tfp_lfile,".")
    if (os.path.isfile(tfp_lfile_x4) or os.path.isfile(tfp_lfile_x5)):
      if verbose: print("Local file exists:",tfp_lfilename,"not upgrading")
    else:
      print("Local file does not exist:",tfp_lfilename," upgrading")
      if os.path.isfile(tfp_lzippath): 
        if verbose: print("Local zip file does exist: "+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip - skipping download.")
      else:
        if verbose: print("Local zip file does not exist: "+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip")
        urllib.request.urlretrieve(tfp_url, tfp_lzippath)
      zfile = zipfile.ZipFile(tfp_lzippath)
      zfile.extractall(plugins_dir)
      zfile.close
      if os.path.isfile(tfp_lfile_x5):
        tfp_lfile = tfp_lfile_x5  
      if os.path.isfile(tfp_lfile_x4):
        tfp_lfile = tfp_lfile_x4
      os.chmod(tfp_lfile, 0o755)

tf_url = release_url+"terraform/"
if debug : print(tf_url)
webcontent = requests.get(tf_url)
if debug : print(webcontent)
html_content = html.fromstring(webcontent.content)
nodes = html_content.xpath('/html/body/ul/li/a/text()')
for x in range(1,10,1):
   nonrelease = ["alpha","beta"]
   tfp_filename=nodes[x]
   if not re.compile("|".join(nonrelease),re.IGNORECASE).search(tfp_filename): break

tfp_version=remove_prefix(tfp_filename, "terraform_")
tfp_lfilename="terraform_"+tfp_version+""
tfp_url = tf_url+tfp_version+"/"+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip"
tfp_lzippath = tmp_dir+"/"+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip"
if debug : print(tfp_url)
if debug : print(tfp_lfilename)
tfp_lfile = Path(tf_dir+"/"+tfp_lfilename)
if debug : print(tfp_lfile)
if os.path.isfile(tfp_lfile):
 if verbose: print("Local file exists:",tfp_lfilename,"not upgrading")
else:
 print("Local file does not exist:",tfp_lfilename," upgrading.")
 if os.path.isfile(tfp_lzippath):
    if verbose: print("Local zip file does exist: "+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip")
 else:
    print("Local zip file does not exist: "+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip")
    urllib.request.urlretrieve(tfp_url, tfp_lzippath)

 zfile = zipfile.ZipFile(tfp_lzippath)
 zfile.extract("terraform",tmp_dir)
 zfile.close
 if os.path.isfile(tmp_dir+"/terraform"):
   if os.path.isfile(tf_dir+"/terraform"): os.remove(tf_dir+"/terraform")
   if debug : print(tmp_dir+"/terraform")
   if debug : print(tfp_lfile)
   if debug : print(tf_dir+"/terraform")
   if os.path.isfile(tmp_dir+"/terraform"):
     shutil.move(tmp_dir+"/terraform",tfp_lfile)
     if debug : print("File: "+tmp_dir+"/terraform - does exist renaming..")
   else:
     if debug : print("File: "+tmp_dir+"/terraform - does not exist cant rename..")
   if os.path.isfile(tfp_lfile):
     os.chmod(tfp_lfile, 0o755)
     os.symlink(tfp_lfile,tf_dir+"/terraform")
   else:
     print("Error - File: "+tfp_lfile+" - does not exist - failed to install..")




