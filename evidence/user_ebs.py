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

from helpers import *

#
######################
#
class EvidenceSchedulingUser(Component):
    implements(IRequestHandler, ITemplateProvider)
    
    # IRequestHandler methods
    def match_request(self, req):
        return re.match(r'/ebs/user/[\w_][\d\w_]+/?$', req.path_info)
    
    def process_request(self, req):
        return self.user_info(req)

    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    get_htdocs_dirs = get_templates_dirs
    
    def user_info(self, req):
        user = re.match(r'/ebs/user/([\w_][\d\w_]+)/?$', req.path_info).group(1)
        db = self.env.get_db_cnx()
        velocities, hist = get_estimation_history(db, user)
        avg = float(sum(velocities) / len(velocities))

        latest = [
            {
                'cont': "%.1f" % (hist[tick_id]['time_total'] / hist[tick_id]['time_estimated']),
                'href' : req.href.ticket(tick_id),
                'title' : 'ticket #%d - %s' % (tick_id, hist[tick_id]['title']),
                
            }
                for tick_id in sorted(hist.keys(), key=lambda tid: hist[tid]['changetime'])[-10:]
        ]
            
            
        data = {
            'user' : user, 
            'chart': charts.user_scattered([(hist[tick_id]['time_estimated'], hist[tick_id]['time_total']) for tick_id in hist], avg),
            'vel': '%.2f' % avg,
            'latest' : latest, #", ".join(latest),
        }
        
        return 'user.html', data, None
