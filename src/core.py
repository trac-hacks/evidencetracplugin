#Hello world plugin

import re
import random
import time
           
from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.env import Environment

def get_estimation_history(db, owner):
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
    
    ret = map(lambda r: r[0]/r[1], zip(*res.values()))
    return (ret, zip(*res.values())) if len(ret) > 0 else ([2], [(1,2)])


class EvidanceSchedulingTicket(Component):
    implements(IRequestHandler, ITemplateProvider)
    
    # IRequestHandler methods
    def match_request(self, req):
        self.log.error("*** request : %r ***", req)
        return re.match(r'/ticket/[\d]+/ebs/?$', req.path_info)
    
    def process_request(self, req):
        return self.ticket_info(req)

    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs 
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def ticket_estimate_time(self, ticket_id, owner):
        db = self.env.get_db_cnx()
        history, tmp = get_estimation_history(db, owner)
        cursor = db.cursor()
        cursor.execute("SELECT value FROM ticket_custom WHERE ticket = %s AND name='estimatedhours' LIMIT 1;", [ticket_id] )
        (ticket_estimate, ) = cursor.fetchone()
        predictions = []
        for i in xrange(100):
            predictions.append( float(ticket_estimate) * history[random.randint(0, len(history)-1)] )
        return sum(predictions) / float(len(predictions))

    def get_workdays(self):
        """
        returns worktime per day of the week
        """
        workdays = {}
        for x in xrange(5):
            workdays[x] = 8
        return workdays     

    def calculate_finish_time(self, work_time):
        """
        Takes the working schedule of the
        programmer under consideration.
        """
        workdays = self.get_workdays()
        
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
                self.log.error("breaking with worktime: %f \n diff: %f" % (work_time, time_diff))
                break
            
            work_time -= workdays[day]
            time_diff += 24
        
        return time.ctime( time.time() + time_diff * 3600 )
            
    
    def ticket_info(self, req):
        """
        Renders the page with the ticket prediction
        """
        ticket_id = re.match(r'/ticket/([\d]+)/ebs$', req.path_info).group(1)
        db = self.env.get_db_cnx()
        
        cursor = db.cursor()
        cursor.execute("SELECT owner FROM ticket WHERE id = %s", [ticket_id])
        owner = cursor.fetchone()[0]
        self.log.error("*** Ticked id : %r | owner: %s ***" % (ticket_id, owner))
        predicted_hours = self.ticket_estimate_time(ticket_id, owner)
        
        date = self.calculate_finish_time(predicted_hours)
        data = {
            'hours_left':predicted_hours,
            'date': date,
            'today': time.ctime(),
        }
        # This tuple is for Genshi (template_name, data, content_type)
        # Without data the trac layout will not appear.
        return 'evidance.html', data, None
    

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
        pass
