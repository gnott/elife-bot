import boto.swf
import json
import random
import datetime
import calendar
import time
import os
import zipfile
import shutil

import activity

import boto.s3
from boto.s3.connection import S3Connection

"""
UnzipFullArticle activity
"""

class activity_UnzipFullArticle(activity.activity):
  
    def __init__(self, settings, logger, conn = None, token = None, activity_task = None):
        activity.activity.__init__(self, settings, logger, conn, token, activity_task)
    
        self.name = "UnzipFullArticle"
        self.version = "1"
        self.default_task_heartbeat_timeout = 30
        self.default_task_schedule_to_close_timeout = 60*5
        self.default_task_schedule_to_start_timeout = 30
        self.default_task_start_to_close_timeout= 60*5
        self.description = "Download a S3 object for a full article, unzip and save to the elife-cdn bucket."
        
        # Local directory settings
        self.TMP_DIR = self.get_tmp_dir() + os.sep + "tmp_dir"
        self.INPUT_DIR = self.get_tmp_dir() + os.sep + "input_dir"
        self.OUTPUT_DIR = self.get_tmp_dir() + os.sep + "output_dir"
        
        self.elife_id = None
        self.document = None
        
        self.pdf_subfolder = 'pdf'
        self.figures_pdf_subfolder = 'figures-pdf'
        self.supp_subfolder = 'suppl'
        
        self.input_bucket = settings.publishing_buckets_prefix + settings.production_bucket
        self.output_bucket = self.settings.cdn_bucket
        
        # For copying to crossref outbox from here for now
        self.crossref_outbox_folder = "crossref/outbox/"
        # Copy to PMC outbox
        self.pmc_outbox_folder = "pmc/outbox/"
        

    def do_activity(self, data = None):
        """
        Do the work
        """
        if(self.logger):
          self.logger.info('data: %s' % json.dumps(data, sort_keys=True, indent=4))
        
        self.elife_id = self.get_elife_id_from_data(data)
        
        # Download the S3 object
        self.document = self.get_document_from_data(data)
        
        # Create output directories
        self.create_activity_directories()
        
        # Download the S3 objects
        self.download_files_from_s3(self.document)
        
        filename = self.INPUT_DIR + os.sep + self.document
        # Unzip article file
        self.unzip_or_move_file(filename, self.TMP_DIR)
        
        # Rename files, if necessary
        self.rename_files()
        
        self.upload_xml()
        self.upload_pdf()
        self.upload_figures_pdf()
        self.upload_supp()
    
        if(self.logger):
          self.logger.info('UnzipFullArticle: %s' % self.elife_id)
    
        if self.xml_file_name():
            #print self.xml_file_name()
            
            # Copy to the crossref outbox here for now, until it is safe to add to ArticleToOutbox activity
            crossref_outbox_file_list = []
            crossref_outbox_file_list.append(self.OUTPUT_DIR + os.sep + self.xml_file_name())
            self.upload_files_to_poa_packaging_bucket(prefix = self.crossref_outbox_folder,
                                                      file_list = crossref_outbox_file_list)
            
            # TODO!! Only send VoR files to the PMC outbox, right now we will upload all there
            pmc_outbox_file_list = crossref_outbox_file_list
            self.upload_files_to_poa_packaging_bucket(prefix = self.pmc_outbox_folder,
                                                      file_list = pmc_outbox_file_list)
            
            # Continue with a standard publish article workflow
            self.start_publish_article_workflow(self.elife_id, self.xml_file_name())
    
        return True
    
    def get_elife_id_from_data(self, data):
        self.elife_id = data["data"]["elife_id"]
        return self.elife_id
  
    def get_document_from_data(self, data):
        self.document = data["data"]["document"]
        return self.document
  
    def rename_files(self):
        to_dir = self.OUTPUT_DIR
        for file_name in self.file_list(self.TMP_DIR):
            if 'media' in file_name or self.file_extension(file_name) == 'tif':
                # Skip it
                continue
            
            new_file_name = self.rename_file(self.file_name_from_name(file_name))
            shutil.copyfile(file_name, to_dir + os.sep + new_file_name)
    
    def rename_file(self, file_name):
        if 'figures' in file_name:
            # Remove hyphen from figures PDF so it is compatible wtih our figures PDF API
            file_name = file_name.replace('elife-', 'elife')
        if self.file_extension(file_name) == 'xml':
            # Remove hyphen from the article XML file for better lens compatibility
            file_name = file_name.replace('elife-', 'elife')
        return file_name
    
    def cdn_base_prefix(self, elife_id):
        return 'elife-articles/' + str(elife_id).zfill(5) + '/'
    
    def xml_file_name(self):
        """
        From the folder get the XML file name
        """
        xml_file_name = None
        for file_name in self.file_list(self.OUTPUT_DIR):
            if self.file_extension(file_name) == 'xml':
                xml_file_name = self.file_name_from_name(file_name)
        return xml_file_name
    
    def upload_xml(self):
        """
        Upload XML to CDN
        """
        file_list = []
        for file_name in self.file_list(self.OUTPUT_DIR):
            if self.file_extension(file_name) == 'xml':
                file_list.append(file_name)
        prefix = self.cdn_base_prefix(self.elife_id)
        
        self.upload_files_to_cdn(prefix, file_list)
    
    def upload_pdf(self):
        """
        Upload PDF to CDN
        """
        file_list = []
        for file_name in self.file_list(self.OUTPUT_DIR):
            if self.file_extension(file_name) == 'pdf' and 'figures' not in file_name:
                file_list.append(file_name)
        prefix = self.cdn_base_prefix(self.elife_id) + self.pdf_subfolder + '/'
        
        self.upload_files_to_cdn(prefix, file_list)
    
    def upload_figures_pdf(self):
        """
        Upload figures PDF to CDN
        """
        file_list = []
        for file_name in self.file_list(self.OUTPUT_DIR):
            if self.file_extension(file_name) == 'pdf' and 'figures' in file_name:
                file_list.append(file_name)
        prefix = self.cdn_base_prefix(self.elife_id) + self.figures_pdf_subfolder + '/'
        
        self.upload_files_to_cdn(prefix, file_list)
        
    def upload_supp(self):
        file_list = []
        for file_name in self.file_list(self.OUTPUT_DIR):
            if 'data' in file_name or 'code' in file_name or 'supp' in file_name:
                file_list.append(file_name)
        prefix = self.cdn_base_prefix(self.elife_id) + self.supp_subfolder + '/'
        
        self.upload_files_to_cdn(prefix, file_list)
    
    def upload_files_to_cdn(self, prefix, file_list, content_type = None):
        """
        Actually upload to S3 CDN bucket
        """
        s3_conn = S3Connection(self.settings.aws_access_key_id, self.settings.aws_secret_access_key)
        bucket = s3_conn.lookup(self.output_bucket)
        
        for file_name in file_list:
            s3_key_name = prefix + self.file_name_from_name(file_name)
            s3_key = boto.s3.key.Key(bucket)
            s3_key.key = s3_key_name
            s3_key.set_contents_from_filename(file_name, replace=True)
            if content_type:
                s3_key.set_metadata('Content-Type', content_type)

    def upload_files_to_poa_packaging_bucket(self, prefix, file_list):
        """
        Used for uploading to the crossref outbox, for now
        """
        s3_conn = S3Connection(self.settings.aws_access_key_id, self.settings.aws_secret_access_key)
        bucket = s3_conn.lookup(self.settings.poa_packaging_bucket)
        
        for file_name in file_list:
            s3_key_name = prefix + self.file_name_from_name(file_name)
            s3_key = boto.s3.key.Key(bucket)
            s3_key.key = s3_key_name
            s3_key.set_contents_from_filename(file_name, replace=True)

    def download_files_from_s3(self, document):
        
        if(self.logger):
            self.logger.info('downloading file ' + document)
  
        # Connect to S3 and bucket
        s3_conn = S3Connection(self.settings.aws_access_key_id, self.settings.aws_secret_access_key)
        bucket = s3_conn.lookup(self.input_bucket)
  
        s3_key_name = document
        s3_key = bucket.get_key(s3_key_name)

        filename = s3_key_name.split("/")[-1]

        filename_plus_path = (self.INPUT_DIR
                              + os.sep + filename)
        mode = "wb"
        f = open(filename_plus_path, mode)
        s3_key.get_contents_to_file(f)
        f.close()
  
    def unzip_or_move_file(self, file_name, to_dir, do_unzip = True):
        """
        If file extension is zip, then unzip contents
        If file the extension 
        """
        if (self.file_extension(file_name) == 'zip'
            and do_unzip is True):
            # Unzip
            if(self.logger):
                self.logger.info("going to unzip " + file_name + " to " + to_dir)
            myzip = zipfile.ZipFile(file_name, 'r')
            myzip.extractall(to_dir)
    
        elif self.file_extension(file_name):
            # Copy
            if(self.logger):
                self.logger.info("going to move and not unzip " + file_name + " to " + to_dir)
            shutil.copyfile(file_name, to_dir + os.sep + self.file_name_from_name(file_name))  

    def list_dir(self, dir_name):
        dir_list = os.listdir(dir_name)
        dir_list = map(lambda item: dir_name + os.sep + item, dir_list)
        return dir_list
    
    def folder_list(self, dir_name):
        dir_list = self.list_dir(dir_name)
        return filter(lambda item: os.path.isdir(item), dir_list)
    
    def file_list(self, dir_name):
        dir_list = self.list_dir(dir_name)
        return filter(lambda item: os.path.isfile(item), dir_list)

    def folder_name_from_name(self, input_dir, file_name):
        folder_name = file_name.split(input_dir)[1]
        folder_name = folder_name.split(os.sep)[1]
        return folder_name
    
    def file_name_from_name(self, file_name):
        name = file_name.split(os.sep)[-1]
        return name
    
    def file_extension(self, file_name):
        name = self.file_name_from_name(file_name)
        if name:
            if len(name.split('.')) > 1:
                return name.split('.')[-1]
            else:
                return None
        return None

    def start_publish_article_workflow(self, elife_id, document):
        """
        In here a new FTPArticle workflow is started for the article object supplied
        """
        starter_status = None
        
        starter_status = None
        
        # Compile the workflow starter parameters
        workflow_id = "PublishArticle_" + str(elife_id)
        workflow_name = "PublishArticle"
        workflow_version = "1"
        child_policy = None
        execution_start_to_close_timeout = None
        
        # Input data
        data = {}
        s3_document_url = ('https://s3.amazonaws.com/' + self.output_bucket + '/'
                           + self.cdn_base_prefix(elife_id) + document)
        data['document'] = s3_document_url
        data['elife_id'] = elife_id
        input_json = {}
        input_json['data'] = data
        input = json.dumps(input_json)
        
        # Connect to SWF
        conn = boto.swf.layer1.Layer1(self.settings.aws_access_key_id,
                                      self.settings.aws_secret_access_key)
        
        # Try and start a workflow
        try:
            response = conn.start_workflow_execution(self.settings.domain, workflow_id,
                                                     workflow_name, workflow_version,
                                                     self.settings.default_task_list,
                                                     child_policy,
                                                     execution_start_to_close_timeout, input)
            starter_status = True
        except boto.swf.exceptions.SWFWorkflowExecutionAlreadyStartedError:
            # There is already a running workflow with that ID, cannot start another
            message = 'SWFWorkflowExecutionAlreadyStartedError: There is already a running workflow with ID %s' % workflow_id
            print message
            if(self.logger):
                self.logger.info(message)
            starter_status = False
        
        return starter_status
        
       
    def create_activity_directories(self):
        """
        Create the directories in the activity tmp_dir
        """
        try:
            os.mkdir(self.TMP_DIR)
            os.mkdir(self.INPUT_DIR)
            os.mkdir(self.OUTPUT_DIR)
            
        except:
            pass