# django imports
from django.contrib.flatpages.models import FlatPage
from django.db import IntegrityError
from django.test import TestCase

# reviews imports
from portlets.models import PortletAssignment
from portlets.models import PortletBlocking
from portlets.models import PortletRegistration
from portlets.models import Slot
import portlets.utils

class MarionetPortletTestCase(TestCase):
    """Tests the models
    """
    def test_portlet(self):
        """
        """
        pass

