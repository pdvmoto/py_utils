#  rt3_ping.py : loop + time heath + ping of connection
#  
# note: make sure records is "too big" for 1 roundtrip ? 

print ( ' ---- rt3.py --- ' )

print ( ' ---- rt3.py first do imports ..--- ' )

import    time
import    string
from      datetime  import  datetime
# import    random

print ( 'for the record: perfcount and process_time: ', time.perf_counter(), time.process_time() )
print ()

# in case we forget..
def f_prfx():
  return " localprfx: "

# local utilities, keep/cp in same directory for now...
from  duration      import *
# from  inspect_obj   import *
from  prefix        import *
from  ora_login     import *


# test code
pp    ()
pp    ( ' ----- imports done, now testing ---- ' )
pp    ()

# print ( ' -- start  : ', tmr_start() )
# print ( ' -- set    : ', tmr_set() )

def f_chatty_info ():
  # 
  # output network and other stats from session 
  # 
  sql_stats = """
    select sn.name, st.value
    --, st.* 
    from v$mystat st
    , v$statname sn
    where st.statistic# = sn.statistic# 
    and ( sn.name like '%roundtrips%'
        or sn.name like 'bytes sent%'
        or sn.name like 'bytes rec%'
        or sn.name like '%execute count%'
        or sn.name like 'user calls'
        or sn.name like 'user commits'
        or sn.name like 'user rollbacks'
        or sn.name like 'consistent gets'
        or sn.name like 'db block gets'
        or sn.name like 'opened cursors current'
        )
      order by sn.name 
  """

  pp ( ' Report out Session Stats ' ) 

  cur_stats = ora_conn.cursor()
  for row in cur_stats.execute ( sql_stats ):
    # pp   ( ' stats : ', row[1], ' ', row[0] )
    pp   ( ' ', f"{row[1]:10d}  {row[0]}"   )

  return 0 # -- -- -- -- f_chatty_info


ora_conn = ora_logon ()
# ora_con2 = ora_logon ()

sql_test = """
  select object_type, count (*)
    from user_objects
   group by object_type
"""

# cur_logon = ora_conn.cursor ()
# for row in cur_logon.execute ( sql_test ):
#   pp   ( ' ora_result : ', row )

pp    ()
pp    ( ' ----- ora_logon: done ---- ' )
pp    ()

def f_rt_1ping ( ora_conn ):

  n_start = time.perf_counter_ns()        # use nano for precision?
  ora_conn.ping()
  n_ms_ping = ( time.perf_counter_ns() - n_start ) / (1000 * 1000 )

  return n_ms_ping  # -- measure 1 ping.. in ms 


# run ping until contol-C, 
# future version: try to spend ping-time inside DB to equalize time spent

def f_run_pings ( ora_conn ):

  n_total_ns = 0
  n_counter  = 0
  service_name = ora_conn.service_name

  while True:

    try: 
      ## hit_enter = input ( "hit enter for next, Contr-C to quit ... " )
      # suggestion: 0=run forever, n>0=run n records, enter=> n=1

      n_start = time.perf_counter_ns()
      ora_conn.ping()
      n_pingtime_ns = time.perf_counter_ns() - n_start 
      n_total_ns += n_pingtime_ns
      
      print ( 'db_ping: ', service_name, ' seq=', n_counter, ' time=', round ( n_pingtime_ns / (1000 * 1000 ), 3), 'ms' )

      n_counter += 1
      time.sleep( 0.01 )

    except KeyboardInterrupt:
      pp ( '\ndb_ping: --- Interrupted, db-ping statisticss:ing ---' ) 
      break

  # -- -- end-While-True -- -- 

  n_avg_ms = n_total_ns / (n_counter * 1000 * 1000 )

  print ('db_ping: ', service_name, ' avg of ', n_counter, 'pings =', round ( n_avg_ms, 3), 'ms\n' )

  return n_avg_ms


def f_do_pings ( n_secs ):
  #
  # loop for n_secs, and report the counter of nr loops done.
  #

  n_count = 0
  n_start = time.perf_counter()
  while time.perf_counter() - n_start < n_secs:
    n_count += 1    # empty loop 

  ms_p_loop = 1000.0 * n_secs/n_count 

  pp (' ' )
  pp ( 'nr empty loops : ', n_count, ' loops/sec: ', n_count/n_secs )
  pp ( 'ms per loop    : ', ms_p_loop )
  pp (' ' )

  # n_count = 0
  # n_start = time.perf_counter()
  # while time.perf_counter() - n_start < n_secs:
  #   n_count += 1
  #   ora_conn.is_healthy()

  # ms_p_health = 1000.0 * n_secs/n_count 

  # pp (' ' )
  # pp ( 'nr empty health : ', n_count, ' loops/sec: ', n_count/n_secs )
  # pp ( 'ms per health   : ', ms_p_health )
  # pp (' ' )

  n_count = 0
  n_start = time.perf_counter()
  while time.perf_counter() - n_start < n_secs:
    n_count += 1
    ora_conn.ping()     # The Actual Ping, for n_sec.

  ms_p_ping = 1000.0 * n_secs/n_count 

  pp (' ' )
  pp ( 'nr empty ping       : ', n_count, ' loops/sec: ', n_count/n_secs )
  pp ( 'ms per ping         : ', ms_p_ping )
  pp ( 'ms per empty loop   : ', ms_p_loop )
  pp ( 'ms ping minus empty : ', (ms_p_ping - ms_p_loop) , 'ms (netto) ' )
  pp (' ' )

  return  n_secs #  -- -- -- roundtrips...

def f_rt_calibrate ( ora_conn, n_secs ):
  #
  # measure the ms for a ping to ora_conn
  # return ms per ping 
  #

  n_count = 0
  end_time   = time.perf_counter() + n_sec
  while time.perf_counter() < end_time:
    n_count += 1    # empty loop 

  ms_p_loop = 1000.0 * n_secs/n_count 

  pp (' ' )
  pp ( 'rt_calibrate: nr empty loops : ', n_count, ' loops/sec: ', n_count/n_secs )
  pp ( 'rt_calibrate: ms per loop    : ', ms_p_loop )
  pp (' ' )

  n_count = 0
  end_time   = time.perf_counter() + n_sec
  while time.perf_counter() < end_time:
    n_count += 1
    ora_conn.ping()     # The Actual Ping, for n_sec.

  ms_p_ping = 1000.0 * n_secs/n_count 

  pp (' ' )
  pp ( 'rt_calibrate: nr pings            : ', n_count, ' ( ', n_count/n_secs, ') pings/sec' )
  pp ( 'rt_calibrate: ms per ping         : ', ms_p_ping )
  pp ( 'rt_calibrate: ms per empty loop   : ', ms_p_loop )
  pp ( 'rt_calibrate: ms ping minus empty : ', (ms_p_ping - ms_p_loop) , 'ms (netto) ' )
  pp (' ' )

  return  ms_p_ping       #  -- -- -- avg ping time..

def f_do_sql ( n_secs ):
  # 
  #  do SQL-fetches, and report time and ms per loop
  # 
  sql_dual = """ 
    select to_number ( to_char ( sysdate, 'SS' ) ) from dual
  """
  # or..return 1 row, 1 value, easiest cursor to read...
  sql1_cnt = """ select count (*) as cnt from rt1 where payload like :b_payl """
  # sql1_cnt = """ select count (*) as cnt from dual """

  cur_cnt = ora_conn.cursor()

  n_count = 0
  n_total = 0
  n_start = time.perf_counter()
  while time.perf_counter() - n_start < n_secs:
    n_count += 1

    # randome string of 3..
    s_payl = '%' + ''.join(random.choices(string.ascii_uppercase, k=3)) + '%'
    # cur_cnt.execute ( sql1_cnt )
    cur_cnt.execute ( sql1_cnt, b_payl=s_payl )
    rows = cur_cnt.fetchall ()

    # pp (' cur1 fetched like: ',   s_payl, ' row-0:', rows[0], rows[0][0] )
    n_total += rows[0][0]

  ms_sql = 1000.0 * n_secs/n_count 

  pp (' ' )
  pp ( 'n_total         : ', n_total )
  pp ( 'nr dual-fetches : ', n_count, ' loops/sec: ', n_count/n_secs )
  pp ( 'ms per fetch    : ', ms_sql )
  pp (' ' )

  return n_secs # -- -- -- f_do_sql, looped over sql


pp    ()
pp    ( ' ----- functions defined, start of MAIN ----- ' )
pp    ()

# check for 1 ping..
pp ( ' single ping : ', f_rt_1ping ( ora_conn ), 'ms' )

# try loop-call of 1 ping..
n_total = 0.0
n_counter = 100
for n_loop in range (1,n_counter):
  n_total += f_rt_1ping ( ora_conn ) 

n_avg = n_total / n_counter
pp ( ' avg of pings : ', n_avg, ' (over ', n_counter, 'pings)' )

# for n_seconds ..
n_sec = 2

# 
ora_sess_inf2 ( ora_conn )

f_rt_calibrate ( ora_conn, n_sec )

# f_do_sql ( n_sec )

pp    ()
pp    ( ' ----- pings done ----- ' )
pp    ()

# show stats for this connection..
ora_sess_inf2 ( ora_conn )

n_avg_ms = f_run_pings ( ora_conn )

pp ( ' ' )
pp ( ' avg pingtime returned: ', n_avg_ms, 'ms' )

tmr_report_time () 

pp    ()
pp ( ' ----- roundtrips done -----' ) 

