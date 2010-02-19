
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

from trac.util import Markup
from trac.web.href import Href
from genshi.filters.transform import Transformer

#
######################
#

def ticket_finish(db, ticket_id):
    predicted_hours = ticket_estimate_time(db, ticket_id)
    if(predicted_hours == 0): return (0, 'unknown')
    return ( predicted_hours, calculate_finish_time(predicted_hours) )

#
######################
#

def get_estimation_history(db, owner):
    """
        returns (
                  [ <coef1>, <coef2>, <coef3> ],
                  [(<estimate1, actual1>), (<estimate2, actual2>), (<estimate3, actual3>)..]
                )
    """
    cursor = db.cursor()
    res = {}
    for field in ['totalhours', 'estimatedhours']:
        cursor.execute("""SELECT
                            tc.value
                        FROM
                            ticket_custom tc
                          LEFT JOIN
                            ticket t ON tc.ticket = t.id
                        WHERE
                            t.owner = %s AND
                            t.status = 'closed' AND
                            tc.name = %s AND
                            tc.value > 0""", [owner, field] )
        
        res[field] = [ float(v[0]) for v in cursor ]
    hist = filter( lambda t: t[1] > 0 and t[0] > 0,  zip(*res.values()) )
    ret = map(lambda r: r[0]/r[1], hist)
    return (ret, zip(*res.values())) if len(ret) > 0 else ([2], [(1,2)])

#
######################
#
def ticket_estimate_time(db, ticket_id):
    """
    Returns the predicted work time in hours for this ticket
    """
    cursor = db.cursor()
    cursor.execute("SELECT owner FROM ticket WHERE id = %s", [ticket_id])
    owner = cursor.fetchone()[0]
    
    history, tmp = get_estimation_history(db, owner)
    cursor = db.cursor()
    cursor.execute("SELECT value FROM ticket_custom WHERE ticket = %s AND name='estimatedhours' LIMIT 1;", [ticket_id] )
    (ticket_estimate, ) = cursor.fetchone()
    if(ticket_estimate == 0): return 0
    predictions = []
    for i in xrange(100):
        predictions.append( float(ticket_estimate) * history[random.randint(0, len(history)-1)] )
    return sum(predictions) / float(len(predictions))

#
######################
#
def get_workdays():
    """
    returns worktime per day of the week
    """
    workdays = {}
    for x in xrange(5):
        workdays[x] = 8
    return workdays

#
######################
#
def calculate_finish_time(work_time):
    """
    Takes the working schedule of the
    programmer under consideration.
    """
    workdays = get_workdays()

    start_workday, end_workday = 9, 18
    day = time.localtime().tm_wday
    this_hour = time.localtime().tm_hour + time.localtime().tm_min/60.0
    time_diff = 0.0

    if(day in workdays and this_hour > start_workday and this_hour < end_workday):
        if(end_workday - this_hour > work_time):
            time_diff += work_time
            work_time = 0
        else:
            work_time -= end_workday - this_hour
            day += 1
            time_diff += 24 - this_hour + start_workday
    else:
        if(this_hour < start_workday):
            time_diff += start_workday - this_hour
        else:
            day += 1
            time_diff += 24 - this_hour + start_workday

    day = day % 7
    while(work_time):
        while(not day in workdays):
            day = (day + 1) % 7
            time_diff += 24

        if(work_time < workdays[day]):
            time_diff += work_time
            break
        
        work_time -= workdays[day]
        time_diff += 24
        day = (day + 1) % 7

    return time.ctime( time.time() + time_diff * 3600 )
    

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
        tmp, hist = get_estimation_history(db, user)
        uchart = charts.user_scattered(hist)
        
        return 'user.html', {'user' : user, 'chart': uchart}, None


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

class TicketWebUiAddon(Component):
    implements(ITemplateStreamFilter)
    
    def __init__(self):
        pass

    # ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        self.log.debug("EBS TicketWebUiAddon executing") 
        if not filename == 'ticket.html':
            self.log.debug("EBS TicketWebUiAddon not the correct template")
            return stream
        self.log.error(req.path_info)
        db = self.env.get_db_cnx()
        m = re.match(r'.*ticket/([\d]+).*', req.path_info)
        if(m==None): return stream
        ticket_id = m.group(1)
        stream = stream | Transformer('//div[@id="ticket"]').after(
                                                                tag.a("Predicted finish date: %s" % ticket_finish(db,ticket_id)[1],  href = req.href.ticket('/%s/ebs' % ticket_id))()
                                                                    )
        return stream