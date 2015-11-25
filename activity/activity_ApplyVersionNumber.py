import activity
import json
import os
import re
from os import path
from jats_scraper import jats_scraper
import boto.s3
from boto.s3.key import Key
from boto.s3.connection import S3Connection
from S3utility.s3_notification_info import S3NotificationInfo
from provider.execution_context import Session
from provider.article_structure import ArticleInfo
import provider.s3lib as s3lib
from elifetools import xmlio

"""
ApplyVersionNumber.py activity
"""


class activity_ApplyVersionNumber(activity.activity):
    def __init__(self, settings, logger, conn=None, token=None, activity_task=None):
        activity.activity.__init__(self, settings, logger, conn, token, activity_task)

        self.name = "ApplyVersionNumber"
        self.version = "1"
        self.default_task_heartbeat_timeout = 30
        self.default_task_schedule_to_close_timeout = 60 * 5
        self.default_task_schedule_to_start_timeout = 30
        self.default_task_start_to_close_timeout = 60 * 5
        self.description = "Rename expanded article files on S3 with a new version number"
        self.logger = logger

    def do_activity(self, data=None):
        """
        Do the work
        """

        self.expanded_bucket_name = self.settings.publishing_buckets_prefix + self.settings.expanded_bucket

        info = S3NotificationInfo.from_dict(data)
        session = Session(self.settings)
        version = session.get_value(self.get_workflowId(), 'version')
        article_id = session.get_value(self.get_workflowId(), 'article_id')
        article_version_id = article_id + '.' + version
        run = session.get_value(self.get_workflowId(), 'run')

        self.emit_monitor_event(self.settings, article_id, version, run, "ApplyVersionNumber", "start",
                                "Starting applying version number to files for " + article_id)

        try:

            if self.logger:
                self.logger.info('data: %s' % json.dumps(data, sort_keys=True, indent=4))
                
            # Do not rename files if a version number is in the file_name
            m = re.search(ur'-v([0-9]*?)[\.|-]', info.file_name)
            
            if m is not None:
                # Nothing to do
                pass
            
            elif m is None and version is not None:
                expanded_folder_name = session.get_value(self.get_workflowId(), 'expanded_folder')
                bucket_folder_name = expanded_folder_name.replace(os.sep, '/')
                self.rename_article_s3_objects(bucket_folder_name, version)
                
            self.emit_monitor_event(self.settings, article_id, version, run, "Apply Version Number", "end",
                        "Finished applying version number to article " + article_id +
                        " for version " + version + " run " + str(run))


        except Exception as e:
            self.logger.exception("Exception when applying version number to article")
            self.emit_monitor_event(self.settings, article_id, version, run, "Convert JATS", "error",
                                    "Error in applying version number to files for " + article_id +
                                    " message:" + e.message)

        return True

    def rename_article_s3_objects(self, bucket_folder_name, version):
        """
        Main function to rename article objects on S3
        and apply the renamed file names to the article XML file
        """
        
        # Connect to S3 and bucket
        s3_conn = S3Connection(self.settings.aws_access_key_id, self.settings.aws_secret_access_key,
                               host=self.settings.s3_hostname)
        bucket = s3_conn.lookup(self.expanded_bucket_name)
        
        # bucket object list
        s3_key_names = s3lib.get_s3_key_names_from_bucket(
            bucket          = bucket,
            prefix          = bucket_folder_name + "/")

        # Get the old name to new name map
        file_name_map = self.build_file_name_map(s3_key_names, version)

        # log file names for reference
        if self.logger:
            self.logger.info('file_name_map: %s' % json.dumps(file_name_map, sort_keys=True, indent=4))

        # rename_s3_objects(old_name_new_name_dict)
        self.rename_s3_objects(bucket, self.expanded_bucket_name, bucket_folder_name, file_name_map)
        
        # rewrite_and_upload_article_xml()
        xml_filename = self.find_xml_filename_in_map(file_name_map)
        self.download_file_from_bucket(bucket, bucket_folder_name, xml_filename)
        self.rewrite_xml_file(xml_filename, file_name_map)
        self.upload_file_to_bucket(bucket, bucket_folder_name, xml_filename)

    def download_file_from_bucket(self, bucket, bucket_folder_name, filename):
        
        key_name = bucket_folder_name + '/' + filename
        key = Key(bucket)
        key.key = key_name
        local_file = self.open_file_from_tmp_dir(filename, mode='wb')
        key.get_contents_to_file(local_file)
        local_file.close()
        
    def rewrite_xml_file(self, xml_filename, file_name_map):
        
        local_xml_filename = path.join(self.get_tmp_dir(), xml_filename)
        
        xmlio.register_xmlns()
        root = xmlio.parse(local_xml_filename)
        
        # Convert xlink href values
        total = xmlio.convert_xlink_href(root, file_name_map)
        
        # Start the file output
        reparsed_string = xmlio.output(root)
        f = open(local_xml_filename, 'wb')
        f.write(reparsed_string)
        f.close()
        
    def upload_file_to_bucket(self, bucket, bucket_folder_name, filename):

        local_filename = path.join(self.get_tmp_dir(), filename)
        key_name = bucket_folder_name + '/' + filename
        key = Key(bucket)
        key.key = key_name
        key.set_contents_from_filename(local_filename)

        
    def build_file_name_map(self, s3_key_names, version):
        
        file_name_map = {}
        
        for key_name in s3_key_names:
            filename = key_name.split("/")[-1]
                        
            # Get the new file name
            file_name_map[filename] = None
            
            if self.is_video_file(filename) is False:
                renamed_filename = self.new_filename(filename, version)
            else:
                # Keep video files named the same
                renamed_filename = filename
            
            if renamed_filename:
                file_name_map[filename] = renamed_filename
            else:
                if(self.logger):
                    self.logger.info('there is no renamed file for ' + filename)
 
        return file_name_map

    def new_filename(self, old_filename, version):
        (file_prefix, file_extension) = self.file_parts(old_filename)
        new_filename = file_prefix + '-v' + str(version) + '.' + file_extension
        return new_filename

    def rename_s3_objects(self, bucket, bucket_name, bucket_folder_name, file_name_map):
        # Rename S3 bucket objects directly
        for old_name,new_name in file_name_map.iteritems():
            # Do not need to rename if the old and new name are the same
            if old_name == new_name:
                continue
            
            if new_name is not None:
                old_s3_key = bucket_folder_name + '/' + old_name
                new_s3_key = bucket_folder_name + '/' + new_name
                
                # copy old key to new key
                key = bucket.copy_key(new_s3_key, bucket_name, old_s3_key)
                if(isinstance(key, boto.s3.key.Key)):
                    # delete old key
                    old_key = bucket.delete_key(old_s3_key)


    def find_xml_filename_in_map(self, file_name_map):
        for old_name,new_name in file_name_map.iteritems():
            info = ArticleInfo(new_name)
            if info.file_type == 'ArticleXML':
                return new_name


    def file_parts(self, filename):
        prefix = filename.split('.')[0]
        extension = filename.split('.')[-1]
        return (prefix, extension)


    def is_video_file(self, filename):
        """
        Simple check for video file names
        E.g. match True on elife-00005-media1.mov
             match True on elife-99999-resp-media1.avi
             match False on elife-00005-media1-code1.wrl
        """
        
        (file_prefix, file_extension) = self.file_parts(filename)
        file_type_plus_index = file_prefix.split('-')[-1]
        if "media" in file_type_plus_index:
            return True
        else:
            return False

    @staticmethod
    def get_article_xml_key(bucket, expanded_folder_name):
        files = bucket.list(expanded_folder_name + "/", "/")
        for bucket_file in files:
            key = bucket.get_key(bucket_file.key)
            filename = key.name.rsplit('/', 1)[1]
            info = ArticleInfo(filename)
            if info.file_type == 'ArticleXML':
                return key, filename
        return None
