import re
from trac.web.api import ITemplateStreamFilter
from trac.log import logger_factory
from trac.core import *
from genshi.builder import tag
from trac.web import IRequestHandler
from trac.util import Markup
from trac.web.href import Href
from genshi.filters.transform import Transformer
from trac.web.api import ITemplateStreamFilter
from helpers import *

class TicketWebUiAddon(Component):
    implements(ITemplateStreamFilter)
    
    def __init__(self):
        pass

    # ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        
        if not filename == 'ticket.html':
            return stream
        
        self.log.error(req.path_info)
        
        db = self.env.get_db_cnx()
        m = re.match(r'.*ticket/([\d]+).*', req.path_info)
        
        if(m==None): return stream
        
        ticket_id = int(m.group(1))
        ticket_ebs_info = ticket_finish(db, ticket_id)

        if not ticket_ebs_info:
            self.log.debug("No ebs info for ticket %d" % ticket_id)
            return stream
        
        time_div = tag.div("Predicted hours to work: %s" % str(ticket_ebs_info[0]))()
        stream = stream | Transformer('//div[@id="ticket"]').after(time_div)

        if data['ticket'].values['status'] == 'closed':
            # no point in showing predicted dates for already closed tickets
            return stream
        
        ahref = tag.a("Predicted finish date: %s" % ticket_ebs_info[1],  href = req.href.ticket('/%d/ebs' % ticket_id))()
        stream = stream | Transformer('//div[@id="ticket"]').after(ahref)
        
        return stream