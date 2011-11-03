import re
import random
import time
           
from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.env import Environment

from trac.web.api import ITemplateStreamFilter
from trac.log import logger_factory

from helpers import *

#
######################
#
class EvidenceSchedulingTicket(Component):
    implements(IRequestHandler, ITemplateProvider)
    
    #
    ######################
    #
    def match_request(self, req):
        """
        IRequestHandler methods
        """
        self.log.error("*** request : %r ***", req)
        return re.match(r'/ticket/[\d]+/ebs/?$', req.path_info)
    #
    ######################
    #
    def process_request(self, req):
        return self.ticket_info(req)

    #
    ######################
    #
    def get_templates_dirs(self):
        """
        ITemplateProvider methods
        Used to add the plugin's templates and htdocs
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    #
    ######################
    #
    get_htdocs_dirs = get_templates_dirs

    #
    ######################
    #
    def ticket_info(self, req):
        """
        Renders the page with the ticket prediction
        """
        ticket_id = re.match(r'/ticket/([\d]+)/ebs/?$', req.path_info).group(1)
        db = self.env.get_db_cnx()
        
        cursor = db.cursor()
        cursor.execute("SELECT owner FROM ticket WHERE id = %s", [ticket_id])
        owner = cursor.fetchone()[0]

        predicted_hours, date = ticket_finish(db, ticket_id)
        data = {
            'hours_left': predicted_hours,
            'date': date,
            'link': tag.a("Programmer's evidence profile", href=req.href.ebs('/user/%s/' % owner)),
            'owner' : owner,
            'ticket_id' : ticket_id,
        }
        # This tuple is for Genshi (template_name, data, content_type)
        # Without data the trac layout will not appear.
        return 'evidence.html', data, None
