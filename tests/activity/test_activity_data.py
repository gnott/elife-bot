import json
import classes_mock

json_output_parameter_example_string = open("tests/test_data/ConvertJATS_json_output_for_add_update_date_to_json.json", "r").read()
json_output_parameter_example = json.loads(open("tests/test_data/ConvertJATS_json_output_for_add_update_date_to_json.json", "r").read())
json_output_return_example = json.loads(open("tests/test_data/ConvertJATS_add_update_date_to_json_return.json", "r").read())
json_output_return_example_string = open("tests/test_data/ConvertJATS_add_update_date_to_json_return.json", "r").read()

xml_content_for_xml_key = open("tests/test_data/ConvertJATS_content_for_test_origin.xml", "r").read()

bucket_origin_file_name = "test_origin.xml"
bucket_dest_file_name = "test_dest.json"

session_example = {
            'version': '1',
            'article_id': '00353',
            'run': '1ee54f9a-cb28-4c8e-8232-4b317cf4beda',
            'expanded_folder': '00353.1/1ee54f9a-cb28-4c8e-8232-4b317cf4beda',
            'update_date': '2012-12-13T00:00:00Z',
        }
key_names = [u'00353.1/1ee54f9a-cb28-4c8e-8232-4b317cf4beda/elife-00353-fig1-v1.tif', u'00353.1/1ee54f9a-cb28-4c8e-8232-4b317cf4beda/elife-00353-v1.pdf',
             u'00353.1/1ee54f9a-cb28-4c8e-8232-4b317cf4beda/elife-00353-v1.xml']

bucket = {
    bucket_origin_file_name: xml_content_for_xml_key,
    bucket_dest_file_name: ""
}

run_example = '1ee54f9a-cb28-4c8e-8232-4b317cf4beda'


PreparePost_session_example = {
            'version': '1',
            'article_id': '00353',
            'run': '1ee54f9a-cb28-4c8e-8232-4b317cf4beda',
            'expanded_folder': '00353.1/1ee54f9a-cb28-4c8e-8232-4b317cf4beda',
            'update_date': '2012-12-13T00:00:00Z',
            'article_version_id': '00353.1',
            'status': 'vor',
            'eif_filename': '00353.1/1ee54f9a-cb28-4c8e-8232-4b317cf4beda/elife-00353-v1.json',
            'article_path': 'content/1/e00353v1'
        }
PreparePostEIF_test_dir = "fake_sqs_queue_container"
PreparePostEIF_message = {'eif_filename': '00353.1/1ee54f9a-cb28-4c8e-8232-4b317cf4beda/elife-00353-v1.json', 'passthrough': {'status': 'vor', 'update_date': '2012-12-13T00:00:00Z', 'run': '1ee54f9a-cb28-4c8e-8232-4b317cf4beda', 'expanded_folder': '00353.1/1ee54f9a-cb28-4c8e-8232-4b317cf4beda', 'version': '1', 'article_path': 'content/1/e00353v1', 'article_id': '00353'}, 'eif_bucket': 'dest_bucket'}
PreparePostEIF_json_output_return_example = json.loads(open("tests/test_data/PreparePostEIF_json_return.json", "r").read())


def PostEIFBridge_data(published):
        return {
                'eif_filename': '00353.1/cf9c7e86-7355-4bb4-b48e-0bc284221251/elife-00353-v1.json',
                'eif_bucket':  'jen-elife-publishing-eif',
                'article_id': u'00353',
                'version': u'1',
                'run': u'cf9c7e86-7355-4bb4-b48e-0bc284221251',
                'article_path': 'content/1/e00353v1',
                'published': published,
                'expanded_folder': u'00353.1/cf9c7e86-7355-4bb4-b48e-0bc284221251',
                'status': u'vor',
                'update_date': u'2012-12-13T00:00:00Z'
            }
PostEIFBridge_test_dir = "fake_sqs_queue_container"
PostEIFBridge_message = {'workflow_name': 'PostPerfectPublication', 'workflow_data': {'status': u'vor', 'update_date': u'2012-12-13T00:00:00Z', 'run': u'cf9c7e86-7355-4bb4-b48e-0bc284221251', 'expanded_folder': u'00353.1/cf9c7e86-7355-4bb4-b48e-0bc284221251', 'version': u'1', 'eif_location': '00353.1/cf9c7e86-7355-4bb4-b48e-0bc284221251/elife-00353-v1.json', 'article_id': u'00353'}}


# ExpandArticle

ExpandArticle_data = {u'event_time': u'2016-06-07T10:45:18.141126Z', u'event_name': u'ObjectCreated:Put', u'file_name': u'elife-00353-vor-v1-20121213000000.zip', u'file_etag': u'1e17ebb1fad6c467fce9cede16bb752f', u'bucket_name': u'jen-elife-production-final', u'file_size': 1097506}
ExpandArticle_data1 = {u'event_time': u'2016-06-07T10:45:18.141126Z', u'event_name': u'ObjectCreated:Put', u'file_name': u'elife-00353-v1-20121213000000.zip', u'file_etag': u'1e17ebb1fad6c467fce9cede16bb752f', u'bucket_name': u'jen-elife-production-final', u'file_size': 1097506}
ExpandArticle_filename = 'elife-00353-vor-v1-20121213000000.zip'
ExpandArticle_path = 'elife-00353-vor-v1'
ExpandArticle_files_source_folder = 'tests/files_source'
ExpandArticle_files_dest_folder = 'tests/files_dest'
ExpandArticle_files_dest_expected = ['elife-00353-fig1-v1.tif', 'elife-00353-v1.pdf', 'elife-00353-v1.xml']
ExpandArticle_files_dest_bytes_expected = [{'name': 'elife-00353-fig1-v1.tif', 'bytes': 961324}, {'name': 'elife-00353-v1.pdf', 'bytes': 936318}, {'name': 'elife-00353-v1.xml', 'bytes': 9458}]

ExpandArticle_data_invalid_article = {u'event_time': u'2016-06-07T10:45:18.141126Z', u'event_name': u'ObjectCreated:Put', u'file_name': u'aaa.zip', u'file_etag': u'1e17ebb1fad6c467fce9cede16bb752f', u'bucket_name': u'jen-elife-production-final', u'file_size': 1097506}
ExpandArticle_data_invalid_version = {u'event_time': u'2016-06-07T10:45:18.141126Z', u'event_name': u'ObjectCreated:Put', u'file_name': u'elife-00353-vor-v-1-20121213000000.zip', u'file_etag': u'1e17ebb1fad6c467fce9cede16bb752f', u'bucket_name': u'jen-elife-production-final', u'file_size': 1097506}

ExpandArticle_data_invalid_status1 = {u'event_time': u'2016-06-07T10:45:18.141126Z', u'event_name': u'ObjectCreated:Put', u'file_name': u'elife-00353-v1.zip', u'file_etag': u'1e17ebb1fad6c467fce9cede16bb752f', u'bucket_name': u'jen-elife-production-final', u'file_size': 1097506}
ExpandArticle_data_invalid_status2 = {u'event_time': u'2016-06-07T10:45:18.141126Z', u'event_name': u'ObjectCreated:Put', u'file_name': u'elife-00353-v1-20121213000000.zip', u'file_etag': u'1e17ebb1fad6c467fce9cede16bb752f', u'bucket_name': u'jen-elife-production-final', u'file_size': 1097506}

lax_article_versions_response_data = {u'1':
                                          {u'rev4_decision': None, u'date_initial_decision': u'2015-05-06',
                                           u'datetime_record_updated': u'2016-05-24T16:45:13.815502Z',
                                           u'date_initial_qc': u'2015-04-29', u'date_rev3_qc': None,
                                           u'title': u'Multiple abiotic stimuli are integrated in the regulation of rice gene expression under field conditions',
                                           u'decision': u'RVF',
                                           u'version': 1, u'date_rev4_decision': None,
                                           u'rev3_decision': None,
                                           u'datetime_record_created': u'2016-02-24T15:11:51.831000Z',
                                           u'type': u'research-article', u'status': u'poa', u'date_full_qc': u'2015-05-13',
                                           u'date_rev3_decision': None, u'date_rev1_qc': u'2015-09-17', u'date_rev1_decision': u'2015-10-13',
                                           u'datetime_submitted': None, u'ejp_type': u'RA', u'volume': 4, u'manuscript_id': 8411, u'doi': u'10.7554/eLife.08411',
                                           u'initial_decision': u'EF', u'rev1_decision': u'RVF', u'rev2_decision': u'AF',
                                           u'date_rev2_qc': u'2015-11-11', u'date_rev2_decision': u'2015-11-25', u'date_rev4_qc': None,
                                           u'date_full_decision': u'2015-06-15', u'website_path': u'content/4/e08411v1',
                                           u'datetime_published': u'2015-11-26T00:00:00Z'},
                                      u'2':
                                          {u'rev4_decision': None, u'date_initial_decision': u'2015-05-06',
                                           u'datetime_record_updated': u'2016-05-24T16:45:13.815502Z', u'date_initial_qc': u'2015-04-29',
                                           u'date_rev3_qc': None,
                                           u'title': u'Multiple abiotic stimuli are integrated in the regulation of rice gene expression under field conditions',
                                           u'decision': u'RVF', u'version': 2, u'date_rev4_decision': None, u'rev3_decision': None,
                                           u'datetime_record_created': u'2016-02-24T15:11:51.831000Z',
                                           u'type': u'research-article', u'status': u'vor', u'date_full_qc': u'2015-05-13', u'date_rev3_decision': None,
                                           u'date_rev1_qc': u'2015-09-17', u'date_rev1_decision': u'2015-10-13', u'datetime_submitted': None,
                                           u'ejp_type': u'RA', u'volume': 4, u'manuscript_id': 8411, u'doi': u'10.7554/eLife.08411',
                                           u'initial_decision': u'EF', u'rev1_decision': u'RVF', u'rev2_decision': u'AF',
                                           u'date_rev2_qc': u'2015-11-11', u'date_rev2_decision': u'2015-11-25', u'date_rev4_qc': None,
                                           u'date_full_decision': u'2015-06-15', u'website_path': u'content/4/e08411v1', u'datetime_published': u'2015-12-31T00:00:00Z'}
                                      }


#ResizeImages

ResizeImages_data = {u'event_time': u'2016-06-14T12:32:38.084176Z', u'event_name': u'ObjectCreated:Put', u'file_name': u'elife-00353-vor-v1-20121213000000.zip', u'file_etag': u'1e17ebb1fad6c467fce9cede16bb752f', u'bucket_name': u'jen-elife-production-final', u'file_size': 1097506}