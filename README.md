# README #

### nso2inode - NSO to Inode mapper script###

This script will scan a bucket containing NetApp NAS Bridge metadata and create an output JSON object that maps 
filenames to inodes.

Version 0.1 released January 2016.


### How do I get set up? ###

Install boto.  
```
#!bash

pip install boto
```

Fill in nso2inode.conf with all the appropriate values.  Below is an actual working version of the nso2inode
file.

[webscaledemo]
access_id = <some access id>
access_secret = <some access secret>
host = webscaledemo.netapp.com
port = 8082
is_secure = True
debug = False
bucket = c01
log = nso2inode.log
output_json = test.json

Run the script by typing in the following:

```
#!bash

python nso2inode.py
```


### You can also run the script with CLI arguments.

```
#!bash

python nso2inode.py -k <some access key> -s <some access secret> -f webscaledemo.netapp.com -p 8082 -d -b c01

```

CLI usage information includes the following:

```
#!bash

usage: nso2inode.py [-h] [-k ACCESS_ID] [-s ACCESS_SECRET] [-f HOST] [-p PORT]
                    [-l IS_SECURE] [--DEBUG] [-c CONFIG_FILE] [-b BUCKET]
                    [--log LOG] [-O OUTPUT_JSON]

optional arguments:
  -h, --help        show this help message and exit
  -k ACCESS_ID      S3 Access Key ID
  -s ACCESS_SECRET  S3 Access Key Secret
  -f HOST           S3 endpoint. This value can be an FQDN or IP address.
  -p PORT           S3 endpoint port. The default for StorageGRID Webscale is
                    8082.
  -l IS_SECURE      Specify if endpoint is SSL encrypted. The default value is
                    True.
  --DEBUG, -d       Set logging level to DEBUG.
  -c CONFIG_FILE    Specify the config file. The default is nso2inode.conf
  -b BUCKET         Bucket containing NAS Bridge data.
  --log LOG         Set log file.
  -O OUTPUT_JSON    Destination file for output. Default is nso2inode.json.
```