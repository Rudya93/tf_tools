import configparser
import requests
import platform
import os
import sys
from pathlib import Path
from lxml import html
import urllib.request
import zipfile

tfver = 0.5
debug = False
p_os      = sys.platform
p_arch   = platform.architecture()[0]

if p_arch == '64bit':
  p_tfarch = 'amd64'
else:
  p_tfarch = '386'

def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]

print("Terraform provider update tool - version:",tfver,"- Arnvid L. Karstad / Basefarm")
print("Running updates for",p_os,p_arch,"/",p_tfarch)

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
    print("Provider:",option,"enabled - checking versions")
    provider_url = release_url+option+"/"
    if debug : print("Grabbing list from:",provider_url)
    webcontent = requests.get(provider_url)
    html_content = html.fromstring(webcontent.content)
    nodes = html_content.xpath('/html/body/ul/li/a/text()')
    tfp_filename=nodes[1]
    tfp_version=remove_prefix(tfp_filename, option+"_")
    tfp_lfilename=option+"_v"+tfp_version+"_x4"
    tfp_url = provider_url+tfp_version+"/"+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip"
    tfp_lzippath = tmp_dir+"/"+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip"
    if debug : print(tfp_url)
    if debug : print(tfp_lfilename)
    tfp_lfile = Path(plugins_dir+"/"+tfp_lfilename)
    if debug : print(tfp_lfile)
    if os.path.isfile(tfp_lfile): 
      print("Local file exists:",tfp_lfilename,"not upgrading")
    else:
      print("Local file does not exist:",tfp_lfilename)
      if os.path.isfile(tfp_lzippath): 
        print("Local zip file does exist: "+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip")
      else:
        print("Local zip file does not exist: "+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip")
        urllib.request.urlretrieve(tfp_url, tfp_lzippath)
      zfile = zipfile.ZipFile(tfp_lzippath)
      zfile.extract(tfp_lfilename,plugins_dir)
      zfile.close
      os.chmod(tfp_lfile, 0o755)

tf_url = release_url+"terraform/"
if debug : print(tf_url)
webcontent = requests.get(tf_url)
if debug : print(webcontent)
html_content = html.fromstring(webcontent.content)
nodes = html_content.xpath('/html/body/ul/li/a/text()')
tfp_filename=nodes[1]
tfp_version=remove_prefix(tfp_filename, "terraform_")
tfp_lfilename="terraform_"+tfp_version+""
tfp_url = tf_url+tfp_version+"/"+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip"
tfp_lzippath = tmp_dir+"/"+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip"
if debug : print(tfp_url)
if debug : print(tfp_lfilename)
tfp_lfile = Path(tf_dir+"/"+tfp_lfilename)
if debug : print(tfp_lfile)
if os.path.isfile(tfp_lfile):
  print("Local file exists:",tfp_lfilename,"not upgrading")
else:
 print("Local file does not exist:",tfp_lfilename)
 if os.path.isfile(tfp_lzippath):
    print("Local zip file does exist: "+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip")
 else:
    print("Local zip file does not exist: "+tfp_filename+"_"+p_os+"_"+p_tfarch+".zip")
    urllib.request.urlretrieve(tfp_url, tfp_lzippath)

 zfile = zipfile.ZipFile(tfp_lzippath)
 zfile.extract("terraform",tmp_dir)
 zfile.close
 if os.path.isfile(tmp_dir+"/terraform"):
   if os.path.isfile(tf_dir+"/terraform"): os.remove(tf_dir+"/terraform")
   os.rename(tmp_dir+"/terraform",tfp_lfile)
   os.chmod(tfp_lfile, 0o755)
   os.symlink(tfp_lfile,tf_dir+"/terraform")

