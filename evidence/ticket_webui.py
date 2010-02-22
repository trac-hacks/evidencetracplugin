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