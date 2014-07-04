"""
CMS Video
"""

import os
import requests
from bok_choy.page_object import PageObject
from bok_choy.promise import EmptyPromise, Promise
from bok_choy.javascript import wait_for_js, js_defined

CLASS_SELECTORS = {
    'video_init': '.is-initialized',
    'video_xmodule': '.xmodule_VideoModule',
    'video_spinner': '.video-wrapper .spinner',
    'video_controls': 'section.video-controls',
    'attach_handout': '.upload-dialog > input[type="file"]',
    'upload_dialog': '.wrapper-modal-window-assetupload',
}

BUTTON_SELECTORS = {
    'handout_download': '.video-handout.video-download-button a',
    'handout_download_editor': '.wrapper-comp-setting.file-uploader .download-action',
    'edit_component': 'a.edit-button',
    'advanced_tab': '.editor-tabs li.inner_tab_wrap:nth-child(2) > a',
    'upload_handout': '.upload-action',
    'handout_submit': '.action-upload',
    'save_settings': '.action-save',
    'handout_clear': '.wrapper-comp-setting.file-uploader .setting-clear',
}


@js_defined('window.Video', 'window.RequireJS.require', 'window.jQuery', 'window.XModule', 'window.XBlock',
            'window.MathJax.isReady')
class VidoComponentPage(PageObject):
    """
    CMS Video Component Page
    """

    url = None

    @wait_for_js
    def is_browser_on_page(self):
        return self.q(css='div{0}'.format(CLASS_SELECTORS['video_xmodule'])).present

    def _wait_for(self, check_func, desc, result=False, timeout=200):
        """
        Calls the method provided as an argument until the Promise satisfied or BrokenPromise

        Arguments:
            check_func (callable): Promise function to be fulfilled.
            desc (str): Description of the Promise, used in log messages.
            result (bool): Indicates whether we need result from Promise or not
            timeout (float): Maximum number of seconds to wait for the Promise to be satisfied before timing out.

        """
        if result:
            return Promise(check_func, desc, timeout=timeout).fulfill()
        else:
            return EmptyPromise(check_func, desc, timeout=timeout).fulfill()

    def wait_for_video_component_render(self):
        """
        Wait until video component rendered completely
        """
        self._wait_for(lambda: self.q(css=CLASS_SELECTORS['video_init']).present, 'Video Player Initialized')
        self._wait_for(lambda: not self.q(css=CLASS_SELECTORS['video_spinner']).visible, 'Video Buffering Completed')
        self._wait_for(lambda: self.q(css=CLASS_SELECTORS['video_controls']).visible, 'Player Controls are Visible')

    def _set_unit_visibility(self, visibility):
        """
        Set unit visibility state

        Arguments:
            visibility (str): private or public

        """
        self.q(css='select[name="visibility-select"] option[value="{}"]'.format(visibility)).first.click()
        self.wait_for_ajax()

    def click_button(self, button_name):
        """
        Click on a button as specified by `button_name`

        Arguments:
            button_name (str): button name

        """
        self.q(css=BUTTON_SELECTORS[button_name]).first.click()
        self.wait_for_ajax()

    def edit_component(self):
        """
        Click on component edit button
        """
        # Currently having issues making a Unit private while creating the course
        # So make the unit private now to edit the component
        self._set_unit_visibility('private')

        self._wait_for(lambda: self.q(css=BUTTON_SELECTORS['edit_component']).visible, 'Component is Editable')
        self.click_button('edit_component')

    def open_advanced_tab(self):
        """
        Click on Advanced Tab.
        """
        self.click_button('advanced_tab')

    def upload_handout(self, handout_filename):
        """
        Upload a handout file to assets

        Arguments:
            handout_filename (str): handout file name

        """
        handout_path = os.sep.join(__file__.split(os.sep)[:-3]) + '/data/uploads/' + handout_filename

        self.click_button('upload_handout')

        self.q(css=CLASS_SELECTORS['attach_handout']).results[0].send_keys(handout_path)

        self.click_button('handout_submit')

        # confirm upload completion
        self._wait_for(lambda: not self.q(css=CLASS_SELECTORS['upload_dialog']).present, 'Upload Handout Completed')

    def save_settings(self):
        """
        Click on settings Save button.
        """
        self.click_button('save_settings')

    def clear_handout(self):
        """
        Clear handout from settings
        """
        self.click_button('handout_clear')

    def _get_handout(self, url):
        """
        Download handout at `url`
        """
        kwargs = dict()

        session_id = [{i['name']: i['value']} for i in self.browser.get_cookies() if i['name'] == u'sessionid']
        if session_id:
            kwargs.update({
                'cookies': session_id[0]
            })

        response = requests.get(url, **kwargs)
        return response.status_code < 400, response.headers

    def download_handout(self, mime_type, is_editor=False):
        """
        Download handout with mime type specified by `mime_type`

        Arguments:
            mime_type (str): mime type of handout file

        Returns:
            tuple: Handout download result.

        """
        selector = BUTTON_SELECTORS['handout_download_editor'] if is_editor else BUTTON_SELECTORS['handout_download']

        handout_url = self.q(css=selector).attrs('href')[0]
        result, headers = self._get_handout(handout_url)

        return result, headers['content-type'] == mime_type

    @property
    def is_handout_button_visible(self):
        """
        Check if handout download button is visible
        """
        return self.q(css=BUTTON_SELECTORS['handout_download']).present and self.q(
            css=BUTTON_SELECTORS['handout_download']).visible
