import re
import random
import time

#
######################
#

def ticket_finish(db, ticket_id):
    predicted_hours = ticket_estimate_time(db, ticket_id)
    if(predicted_hours == 0): return None
    cursor = db.cursor()
    cursor.execute("""SELECT
                            tc.value
                        FROM
                            ticket_custom tc
                        WHERE
                            tc.ticket = %s AND
                            tc.name = %s;
                    """, [str(ticket_id), 'totalhours'] )
    row = cursor.fetchone()
    if not row:
        worked_hours = 0
    else:
        worked_hours = float(row[0])

    hours_left = predicted_hours - worked_hours
    if hours_left < 0: return None
    return ( predicted_hours, calculate_finish_time(hours_left) )

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

    three_months_before = int(time.time())-129600

    cursor.execute("""
        SELECT
            id
        FROM
            ticket
        WHERE
            owner = %s AND
            status = 'closed' AND
            changetime > %s
    """, [str(owner), str(three_months_before)] )

    vector = []
    histstory = []
    
    tickets = [int(row[0]) for row in cursor]

    for ticket in tickets:
        total = 0
        estimated = 0
        
        cursor.execute("""SELECT
                            tc.name,
                            tc.value
                        FROM
                            ticket_custom tc
                        WHERE
                            tc.ticket = %s AND
                            ( tc.name = %s OR tc.name = %s)
                    """, [str(ticket), 'totalhours', 'estimatedhours'] ) # 129600 - 90 дни

        for row in cursor:
            if row[0] == 'estimatedhours':
                estimated = float(row[1])
            else:
                total = float(row[1])

        if total <= 0 or estimated <= 0:
            continue  # with for ticket in tickets

        vector.append(total / estimated)
        histstory.append((estimated, total))
                            
    return (vector, histstory) if len(vector) > 0 else ([2], [(1,2)])

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
