# -*- coding: utf-8 -*-

"""
Acceptance tests for CMS Video Handout.
"""

from unittest import skipIf
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.studio.video.video import VidoComponentPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ..helpers import UniqueCourseTest, is_youtube_available


@skipIf(is_youtube_available() is False, 'YouTube is not available!')
class VideoHandoutBaseTest(UniqueCourseTest):
    """
    CMS Video Handout Base Test Class
    """

    def setUp(self):
        """
        Initialization of pages and course fixture for tests
        """
        super(VideoHandoutBaseTest, self).setUp()

        self.video = VidoComponentPage(self.browser)

        self.outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

    def navigate_to_course_unit(self):
        """
        Install the course with required components and navigate to course unit page
        """
        self._install_course_fixture()
        self._navigate_to_course_unit_page()

    def _install_course_fixture(self):
        """
        Prepare for tests by creating a course with a section, subsection, and unit.
        Performs the following:
            Create a course with a section, subsection, and unit
            Create a user and make that user a course author
            Log the user into studio
        """

        # Create course with Video component
        self.course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc('video', 'Video'),
                    )
                )
            )
        ).install()

        # Auto login and register the course
        AutoAuthPage(
            self.browser,
            staff=False,
            username=self.course_fixture.user.get('username'),
            email=self.course_fixture.user.get('email'),
            password=self.course_fixture.user.get('password')
        ).visit()

    def _navigate_to_course_unit_page(self):
        """
        Open the course from the dashboard and expand the section and subsection and click on the Unit link
        The end result is the page where the user is editing the newly created unit
        """
        # Visit Course Outline page
        self.outline.visit()

        # Visit Unit page
        self.outline.section('Test Section').subsection('Test Subsection').toggle_expand().unit('Test Unit').go_to()

        self.video.wait_for_video_component_render()

    def create_course_with_unit(self, handout_filename, save_settings=True):
        """
        Create a course with unit and also upload handout

        Arguments:
            handout_filename (str): handout file name to be uploaded
            save_settings (bool): save settings or not

        """
        self.navigate_to_course_unit()

        self.video.edit_component()

        self.video.open_advanced_tab()

        self.video.upload_handout(handout_filename)

        if save_settings:
            self.video.save_settings()


class VideoHandoutTest(VideoHandoutBaseTest):
    """
    CMS Video Handout Test Class
    """

    def test_handout_uploads_correctly(self):
        """
        Scenario: Handout uploading works correctly
        Given I have created a Video component with handout file "textbook.pdf"
        Then I can see video button "handout"
        And I can download handout file with mime type "application/pdf"
        """
        self.create_course_with_unit('textbook.pdf')

        self.assertTrue(self.video.is_handout_button_visible)

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))

    def test_handout_download_works_with_save(self):
        """
        Scenario: Handout downloading works correctly w/ preliminary saving
        Given I have created a Video component with handout file "textbook.pdf"
        And I save changes
        And I edit the component
        And I open tab "Advanced"
        And I can download handout file in editor with mime type "application/pdf"
        """
        self.create_course_with_unit('textbook.pdf')

        self.video.edit_component()

        self.video.open_advanced_tab()

        self.assertEqual(self.video.download_handout('application/pdf', is_editor=True), (True, True))

    def test_handout_download_works_wo_save(self):
        """
        Scenario: Handout downloading works correctly w/o preliminary saving
        Given I have created a Video component with handout file "textbook.pdf"
        And I can download handout file in editor with mime type "application/pdf"
        """
        self.create_course_with_unit('textbook.pdf', save_settings=False)

        self.assertEqual(self.video.download_handout('application/pdf', is_editor=True), (True, True))

    def test_handout_clearing_works_w_save(self):
        """
        Scenario: Handout clearing works correctly w/ preliminary saving
        Given I have created a Video component with handout file "textbook.pdf"
        And I save changes
        And I can download handout file with mime type "application/pdf"
        And I edit the component
        And I open tab "Advanced"
        And I clear handout
        And I save changes
        Then I do not see video button "handout"
        """
        self.create_course_with_unit('textbook.pdf')

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))

        self.video.edit_component()

        self.video.open_advanced_tab()

        self.video.clear_handout()

        self.video.save_settings()

        self.assertFalse(self.video.is_handout_button_visible)

    def test_handout_clearing_works_wo_save(self):
        """
        Scenario: Handout clearing works correctly w/o preliminary saving
        Given I have created a Video component with handout file "asset.html"
        And I clear handout
        And I save changes
        Then I do not see video button "handout"
        """
        self.create_course_with_unit('asset.html', save_settings=False)

        self.video.clear_handout()

        self.video.save_settings()

        self.assertFalse(self.video.is_handout_button_visible)

    def test_handout_replace_w_save(self):
        """
        Scenario: User can easy replace the handout by another one w/ preliminary saving
        Given I have created a Video component with handout file "asset.html"
        And I save changes
        Then I can see video button "handout"
        And I can download handout file with mime type "text/html"
        And I edit the component
        And I open tab "Advanced"
        And I replace handout file by "textbook.pdf"
        And I save changes
        Then I can see video button "handout"
        And I can download handout file with mime type "application/pdf"
        """
        self.create_course_with_unit('asset.html')

        self.assertTrue(self.video.is_handout_button_visible)

        self.assertEqual(self.video.download_handout('text/html'), (True, True))

        self.video.edit_component()

        self.video.open_advanced_tab()

        self.video.upload_handout('textbook.pdf')

        self.video.save_settings()

        self.assertTrue(self.video.is_handout_button_visible)

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))

    def test_handout_replace_wo_save(self):
        """
        Scenario: User can easy replace the handout by another one w/o preliminary saving
        Given I have created a Video component with handout file "asset.html"
        And I replace handout file by "textbook.pdf"
        And I save changes
        Then I can see video button "handout"
        And I can download handout file with mime type "application/pdf"
        """
        self.create_course_with_unit('asset.html', save_settings=False)

        self.video.upload_handout('textbook.pdf')

        self.video.save_settings()

        self.assertTrue(self.video.is_handout_button_visible)

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))

    def test_handout_upload_and_clear_works(self):
        """
        Scenario: Upload file "A" -> Remove it -> Upload file "B"
        Given I have created a Video component with handout file "asset.html"
        And I clear handout
        And I upload handout file "textbook.pdf"
        And I save changes
        Then I can see video button "handout"
        And I can download handout file with mime type "application/pdf"
        """
        self.create_course_with_unit('asset.html', save_settings=False)

        self.video.clear_handout()

        self.video.upload_handout('textbook.pdf')

        self.video.save_settings()

        self.assertTrue(self.video.is_handout_button_visible)

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))
