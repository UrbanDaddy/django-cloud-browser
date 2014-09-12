"""Cloud browser template tags."""
import os

from django import template
from django.template import TemplateSyntaxError, Node
from django.template.defaultfilters import stringfilter

from cloud_browser.app_settings import settings

register = template.Library()  # pylint: disable=C0103


@register.filter
@stringfilter
def truncatechars(value, num, end_text="..."):
    """Truncate string on character boundary.

    .. note::
        Django ticket `5025 <http://code.djangoproject.com/ticket/5025>`_ has a
        patch for a more extensible and robust truncate characters tag filter.

    Example::

        {{ my_variable|truncatechars:22 }}

    :param value: Value to truncate.
    :type  value: ``string``
    :param num: Number of characters to trim to.
    :type  num: ``int``
    """
    length = None
    try:
        length = int(num)
    except ValueError:
        pass

    if length is not None and len(value) > length:
        return value[:length-len(end_text)] + end_text

    return value
truncatechars.is_safe = True  # pylint: disable=W0612


@register.tag
def cloud_browser_media_url(_, token):
    """Get base media URL for application static media.

    Correctly handles whether or not the settings variable
    ``CLOUD_BROWSER_STATIC_MEDIA_DIR`` is set and served.

    For example::

        <link rel="stylesheet" type="text/css"
            href="{% cloud_browser_media_url "css/cloud-browser.css" %}" />
    """
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])
    rel_path = bits[1]

    return MediaUrlNode(rel_path)


class MediaUrlNode(Node):
    """Media URL node."""

    #: Static application media URL (or ``None``).
    static_media_url = settings.app_media_url

    def __init__(self, rel_path):
        """Initializer."""
        super(MediaUrlNode, self).__init__()
        self.rel_path = rel_path.lstrip('/').strip("'").strip('"')

    def render(self, context):
        """Render."""
        from django.core.urlresolvers import reverse

        # Check if we have real or Django static-served media
        if self.static_media_url is not None:
            # Real.
            return os.path.join(self.static_media_url, self.rel_path)

        else:
            # Django.
            return reverse("cloud_browser_media",
                           args=[self.rel_path],
                           current_app='cloud_browser')


@register.tag(name='cloud_browser_messages')
def cloud_browser_messages(_, token):
    """Render the grouped (level, tag) django messages.

    For example::

        <div class="cloud_browser_messages success">
            <ul class="messages_list_success"><li>Success</li></ul>
        </div>
        <div class="cloud_browser_messages warning">
            <ul class="messages_list_warning"><li>Warning</li></ul>
        </div>
    """

    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' takes one argument" % bits[0])

    return CloudBrowserMessagesNode(bits[1])


class CloudBrowserMessagesNode(Node):
    """Cloud Browser Messages Node.

    The code is based on:
    http://mrben.co.uk/entry/a-nicer-way-of-using-the-Django-messages-framework
    """

    def __init__(self, messages):
        """Initializer."""
        super(CloudBrowserMessagesNode, self).__init__()
        self.messages = messages

    def render(self, context):
        """Render."""
        messages = context[self.messages]

        classified_messages = dict()
        for msg in messages:
            if (msg.level, msg.tags) in classified_messages:
                classified_messages[(msg.level, msg.tags)].append(msg.message)
            else:
                classified_messages[(msg.level, msg.tags)] = [msg.message]

        messages_template = ""
        for (level, tag) in sorted(classified_messages.iterkeys()):
            messages_template += "<div class='cloud-browser-messages {}'>\n \
            <ul class='messages-list-{}'>".format(tag, tag)
            for message in classified_messages[(level, tag)]:
                messages_template += "<li>{}</li>".format(message)
            messages_template += "</ul>\n</div>\n"

        return messages_template
