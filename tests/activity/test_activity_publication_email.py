import unittest
from activity.activity_PublicationEmail import activity_PublicationEmail
import shutil

from mock import mock, patch
import settings_mock
from classes_mock import FakeLogger
from ddt import ddt, data, unpack
import time

from provider.templates import Templates
from provider.article import article
from provider.ejp import EJP
from provider.simpleDB import SimpleDB

from classes_mock import FakeKey

from testfixtures import TempDirectory

import os
# Add parent directory for imports, so activity classes can use elife-poa-xml-generation
parentdir = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.sys.path.insert(0, parentdir)


@ddt
class TestPublicationEmail(unittest.TestCase):

    def setUp(self):
        fake_logger = FakeLogger()
        self.activity = activity_PublicationEmail(settings_mock, fake_logger, None, None, None)

        self.do_activity_passes = []

        self.do_activity_passes.append({
            "input_data": {},
            "templates_warmed": True,
            "article_xml_filenames": ["elife00013.xml"],
            "article_id": "00013"})

        """
        self.do_activity_passes.append({
            "input_data": {"data": {"allow_duplicates": True}},
            "templates_warmed": True,
            "article_xml_filenames": ["elife00013.xml"],
            "article_id": "00013"})
        """

    def tearDown(self):
        TempDirectory.cleanup_all()
        self.activity.clean_tmp_dir()

    def fake_download_email_templates_from_s3(self, to_dir, templates_warmed):
        template_list = self.activity.templates.get_email_templates_list()
        for filename in template_list:
            source_doc = "tests/test_data/templates/" + filename
            dest_doc = os.path.join(to_dir, filename)
            shutil.copy(source_doc, dest_doc)
        self.activity.templates.email_templates_warmed = templates_warmed

    def fake_download_files_from_s3_outbox(self, xml_filenames, to_dir):
        xml_filename_paths = []
        for filename in xml_filenames:
            source_doc = "tests/test_data/" + filename
            dest_doc = os.path.join(to_dir, filename)
            shutil.copy(source_doc, dest_doc)
            xml_filename_paths.append(dest_doc)
        return xml_filename_paths

    def fake_article_get_folder_names_from_bucket(self):
        return []

    def fake_ejp_get_s3key(self, directory, to_dir, document, source_doc):
        """
        EJP data do two things, copy the CSV file to where it should be
        and also set the fake S3 key object
        """
        dest_doc = os.path.join(to_dir, document)
        shutil.copy(source_doc, dest_doc)
        with open(source_doc, "rb") as fp:
            return FakeKey(directory, document, fp.read())

    def fake_clean_tmp_dir(self):
        """
        Disable the default clean_tmp_dir() when do_activity runs
        so tests can introspect the files first
        Then can run clean_tmp_dir() in the tearDown later
        """
        pass

    @patch.object(activity_PublicationEmail, 'download_files_from_s3_outbox')
    @patch.object(Templates, 'download_email_templates_from_s3')
    @patch.object(article, 'get_folder_names_from_bucket')
    @patch.object(article, 'check_is_article_published_by_lax')
    @patch.object(EJP, 'get_s3key')
    @patch.object(EJP, 'find_latest_s3_file_name')
    @patch.object(SimpleDB, 'elife_add_email_to_email_queue')
    @patch.object(activity_PublicationEmail, 'clean_tmp_dir')
    def test_do_activity(self, fake_clean_tmp_dir, fake_elife_add_email_to_email_queue,
                         fake_find_latest_s3_file_name,
                         fake_ejp_get_s3key, 
                         fake_check_is_article_published_by_lax,
                         fake_article_get_folder_names_from_bucket,
                         fake_download_email_templates_from_s3,
                         fake_download_files_from_s3_outbox):

        directory = TempDirectory()
        fake_clean_tmp_dir = self.fake_clean_tmp_dir()

        for test_data in self.do_activity_passes:

            fake_download_email_templates_from_s3 = self.fake_download_email_templates_from_s3(
                self.activity.get_tmp_dir(), test_data["templates_warmed"])

            fake_download_files_from_s3_outbox.return_value = self.fake_download_files_from_s3_outbox(
                test_data["article_xml_filenames"], self.activity.get_tmp_dir())

            fake_article_get_folder_names_from_bucket.return_value = self.fake_article_get_folder_names_from_bucket()
            fake_check_is_article_published_by_lax.return_value = True
            fake_ejp_get_s3key.return_value = self.fake_ejp_get_s3key(
                directory, self.activity.get_tmp_dir(), "authors.csv", "tests/test_data/ejp_author_file.csv")
            fake_find_latest_s3_file_name.return_value = mock.MagicMock()
            fake_elife_add_email_to_email_queue.return_value = mock.MagicMock()


            success = self.activity.do_activity(test_data["input_data"])

            self.assertEqual(True, success)




if __name__ == '__main__':
    unittest.main()
