import boto
import boto.s3.connection
import json
import logging
import logging.handlers
import argparse
from ConfigParser import SafeConfigParser
import sys

logger = logging.getLogger(__name__)

__author__ = 'Matthew Yee <matthew.yee@netapp.com'


class S3Conn:
    def __init__(self, credential):
        self.conn = boto.connect_s3(
                aws_access_key_id=credential['access_id'],
                aws_secret_access_key=credential['access_secret'],
                host=credential['host'],
                calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                port=credential['port'],
                is_secure=credential['is_secure'],
        )


def parse_arguments():
    credentials = dict(
            access_id='',
            access_secret='',
            host='',
            port='',
            is_secure=True
    )

    log_format = '%(asctime)s %(levelname)s %(message)s'
    log_file = 'nso2inode.log'
    set_debug = False

    parser = argparse.ArgumentParser()

    parser.add_argument('-k', action='store', type=str, dest='access_id',
                        help='S3 Access Key ID')
    parser.add_argument('-s', action='store', type=str, dest='access_secret',
                        help='S3 Access Key Secret')
    parser.add_argument('-f', action='store', type=str, dest='host',
                        help='S3 endpoint. This value can be an FQDN or IP address.')
    parser.add_argument('-p', action='store', type=int, dest='port', default=8082,
                        help='S3 endpoint port. The default for StorageGRID Webscale is 8082.')
    parser.add_argument('-l', action='store', type=bool, dest='is_secure', default=True,
                        help='Specify if endpoint is SSL encrypted. The default value is True.')
    parser.add_argument('--DEBUG', '-d', action='store_true', default=False, dest='level',
                        help='Set logging level to DEBUG.')
    parser.add_argument('-c', action='store', type=str, dest='config_file', default='nso2inode.conf',
                        help='Specify the config file.  The default is nso2inode.conf')
    parser.add_argument('-b', action='store', type=str, dest='bucket',
                        help='Bucket containing NAS Bridge data.')
    parser.add_argument('--log', action='store', type=str, dest='log', default='nso2inode.log',
                        help='Set log file.')
    parser.add_argument('-O', action='store', type=str, dest='output_json', default='nso.json',
                        help='Destination file for output. Default is nso2inode.json.')

    results = parser.parse_args()
    output_json = results.output_json
    bucket = results.bucket
    console = logging.StreamHandler()

    if results.access_id:

        credentials['access_id'] = results.access_id
        credentials['access_secret'] = results.access_secret
        credentials['host'] = results.host
        credentials['port'] = results.port
        credentials['is_secure'] = results.is_secure

        if results.level:
            set_debug = True

        log_file = results.log

    elif results.config_file:
        config = SafeConfigParser()
        config.read(results.config_file)

        section_name = config.sections()[0]
        credentials['access_id'] = config.get(section_name, 'access_id')
        credentials['access_secret'] = config.get(section_name, 'access_secret')
        credentials['host'] = config.get(section_name, 'host')
        credentials['port'] = config.getint(section_name, 'port')
        credentials['is_secure'] = config.getboolean(section_name, 'is_secure')
        bucket = config.get(section_name, 'bucket')
        output_json = config.get(section_name, 'output_json')

        if config.getboolean(section_name, 'debug'):
            set_debug = True

        log_file = config.get(section_name, 'log')

    if set_debug:
        console.setLevel(logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG,
                            filename=log_file,
                            format=log_format,
                            )
    else:
        console.setLevel(logging.INFO)
        logging.basicConfig(level=logging.INFO,
                            filename=log_file,
                            format=log_format
                            )

    formatter = logging.Formatter(log_format)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    logger.debug('CLI arguments: %s', results)

    if bucket == '' or bucket is None:
        logger.info('A bucket must be specified.  This value should be the bucket configured for the NAS Bridge.')
        sys.exit()

    return [credentials, bucket, output_json]


def collect_all_items(credential, bucket):
    item_dict = {"1": {}}
    c1 = S3Conn(credential)
    contents = c1.conn.get_bucket(bucket, validate=False)
    for _ in contents.list():
        logger.debug('Processing bucket items. %s', str(_))
        path_name = _.key.split('/')
        inode = str(contents.get_key(_.name).metadata.get('fs-mapped-inode'))
        object_type = str(contents.get_key(_.name).metadata.get('fs-schema-object-type'))
        if object_type != 'inode' and object_type != 'superblock' and inode != 'None':
            if item_dict.get(path_name[0]):
                item_dict[path_name[0]].update({path_name[1]: inode})
            else:
                item_dict.update({path_name[0]: {path_name[1]: inode}})
    return item_dict


def tree_reduce(tree_dict, original_dict, dir_list_range):
    for k, v in tree_dict.iteritems():
        for i in dir_list_range:
            if v == i:
                tree_dict[k] = original_dict[i]
                # Remove the index from the dir_list_range since we don't need it anymore.
                dir_list_range.remove(i)
                # Recurse
                new_list_range = dir_list_range
                tree_reduce(tree_dict[k], original_dict, new_list_range)
    else:
        return


def build_dir_json(credential, bucket):
    logger.info('Collecting information from bucket %s.', bucket)
    items = collect_all_items(credential, bucket)
    logger.info('Bucket information collection complete.')

    tree_dict = items['1']
    dir_list_range = items.keys()
    dir_list_range.remove('1')
    logger.info('Building directory mapping.')
    tree_reduce(tree_dict, items, dir_list_range)

    return json.dumps(tree_dict, indent=4)


def main():
    # Parse arguments and build the JSON.
    credentials, bucket, output_json = parse_arguments()
    logger.info('Starting.')
    nso_json = build_dir_json(credentials, bucket)

    # Write results.
    logger.info('Writing JSON object: %s', output_json)
    f = open(output_json, 'w')
    f.write(nso_json)
    f.close()
    logger.info('Operation complete.')


if __name__ == '__main__':
    main()
