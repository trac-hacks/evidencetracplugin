
import re
import random
import time
import charts
           
from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.env import Environment

from trac.web.api import ITemplateStreamFilter
from trac.log import logger_factory

from ticket_webui import TicketWebUiAddon
from helpers import *

    

#
######################
#
class EvidanceSchedulingUser(Component):
    implements(IRequestHandler, ITemplateProvider)
    
    # IRequestHandler methods
    def match_request(self, req):
        self.log.error("*** request : %r ***", req)
        return re.match(r'/ebs/user/[\w_][\d\w_]+/?$', req.path_info)
    
    def process_request(self, req):
        return self.user_info(req)

    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    def user_info(self, req):
        user = re.match(r'/ebs/user/([\w_][\d\w_]+)/?$', req.path_info).group(1)
        db = self.env.get_db_cnx()
        velocities, hist = get_estimation_history(db, user)
        avg = float(sum(velocities) / len(velocities))
        data = {
            'user' : user, 
            'chart': charts.user_scattered(hist, avg), 
            'vel': '%.2f' % avg,
            'latest' : ", ".join(map(lambda f: '%.1f'%f, velocities[-10:])),
        }
        
        return 'user.html', data, None


#
######################
#
class EvidanceSchedulingTicket(Component):
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
            'hours_left':predicted_hours,
            'date': date,
            'today': time.ctime(),
            'link': tag.a("Programmer's evidence profile", href=req.href.ebs('/user/%s/' % owner)),
            'owner' : owner,
            'ticket_id' : ticket_id,
        }
        # This tuple is for Genshi (template_name, data, content_type)
        # Without data the trac layout will not appear.
        return 'evidance.html', data, None
