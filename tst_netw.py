#  tst_netw.py : ping a database 
#  

# take this one Early.
# from  duration      import *

print ( ' ---- tst_netw.py --- ' )

print ( ' ---- tst_netw.py first do imports ..--- ' )

import    time
import    string
from      datetime  import  datetime

# in case we forget..
def f_prfx():
  return " localprfx: "

# local utilities, keep/cp in same directory for now...
# from  duration      import *
from  prefix        import *
from  ora_login     import *

pp    ()
pp    ( ' ----- imports done, next def functions, global, constants ---- ' )
pp    ()

# run ping until contol-C, 
# future version: try to spend ping-time inside DB to equalize time spent

def f_run_pings ( ora_conn ):

  n_total_ns = 0
  n_counter  = 0
  service_name = ora_conn.service_name
  dsn_descr    = ora_conn.dsn
  result_list = []

  ping_delay_ms = 1000

  while True:

    try: 
      # suggestion: 0=run forever, n>0=run n records, enter=> n=1

      n_start = time.perf_counter_ns()
      ora_conn.ping()
      n_pingtime_ns = time.perf_counter_ns() - n_start 
      result_list.append ( n_pingtime_ns ) 

      n_total_ns += n_pingtime_ns
      n_counter  += 1
      time.sleep( ping_delay_ms/1000 )

      #print ( 'tst_netw: ', service_name, ' seq=', n_counter, ' time=', round ( n_pingtime_ns / (1000 * 1000 ), 3), 'ms' )
      pp     ( 'tst_netw: ', service_name, ' seq=', n_counter, ' time=', round ( n_pingtime_ns / (1000 * 1000 ), 3), 'ms' )

    except KeyboardInterrupt:
      #pp ( '\ntst_netw: --- Interrupted, db-ping statisticss:ing ---' ) 
      pp ( ' ' )
      break

  # -- -- end-While-True -- -- 

  n_avg_ms = n_total_ns / (n_counter * 1000 * 1000 )

  # calculate min/max/stddev, needed list.
  n_list_sum_ms = sum ( result_list )  / ( 1000 * 1000 )
  n_list_avg_ms = ( n_list_sum_ms / len ( result_list) )
  n_list_min_ms = ( min( result_list ) ) / ( 1000 * 1000 )
  n_list_max_ms = ( max( result_list ) ) / ( 1000 * 1000 )

  n_list_var = 0.0
  for x in result_list:
    n_list_var += ( ( x / ( 1000 * 1000 ) ) - n_list_avg_ms ) ** 2

  # todo: catch n=1 
  if len ( result_list ) <2:
    n_list_stddev = 0
  else:
    n_list_stddev = round ( ( n_list_var / ( len ( result_list ) - 1 ) ) ** 0.5 , 3)

  # back to 3 decimals
  n_list_min_ms = round ( n_list_min_ms, 3 ) 
  n_list_avg_ms = round ( n_list_avg_ms, 3 ) 
  n_list_max_ms = round ( n_list_max_ms, 3 ) 
  n_list_stddev = round ( n_list_stddev, 3 ) 

  # print ('tst_netw: ', service_name, ' avg of ', n_counter, 'pings =', round ( n_avg_ms, 3), 'ms\n' )
  pp ('--', service_name, ' db-ping statisticss: --' )
  pp ('--', n_counter, ' pings to : ', dsn_descr ) 
  pp ('-- round trip min/avg/max/stddev = ' 
                    + f"{n_list_min_ms:.3f}" + '/'
                    + f"{n_list_avg_ms:.3f}" + '/'
                    + f"{n_list_max_ms:.3f}" + '/'
                    + f"{n_list_stddev:.3f}" + 'ms' )

  # pp ( '\n verify avg:', n_avg_ms ) # verified, it was correct..
  # pp ('-- ping delay was ', ping_delay_ms, 'ms' ) 

  return n_avg_ms

# -- -- -- run_pings defined -- -- --


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
  # measure the ms for a ping to ora_conn, return ms per ping 

  n_count_empty = 0
  end_time   = time.perf_counter() + n_sec
  while time.perf_counter() < end_time:
    n_count_empty += 1    # empty loop 

  ms_p_loop = round ( 1000.0 * n_secs/n_count_empty, 6)

  n_count = 0
  end_time   = time.perf_counter() + n_sec
  while time.perf_counter() < end_time:
    n_count += 1
    ora_conn.ping()     # The Actual Ping, for n_sec.

  ms_p_ping = round ( 1000.0 * n_secs/n_count, 6)
  ms_netto  = ms_p_ping - ms_p_loop

  pp (' ' )
  pp ( 'rt_calibr: ping         : ', f"{ms_p_ping:9.6f}", ' ms (', n_count      , 'pings in', n_sec, 'seconds )' )
  pp ( 'rt_calibr: empty loop   : ', f"{ms_p_loop:9.6f}", ' ms (', n_count_empty, 'loops in', n_sec, 'seconds)' )
  pp ( 'rt_calibr: ping - empty : ', f"{ms_netto:9.6f}",  ' ms (netto ping-time) ' )
  pp (' ' )

  return  ms_p_ping       #  -- -- -- rt_calibrate, return avg ping time..

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


def f_rt_1ping ( ora_conn ):

  n_start = time.perf_counter_ns()        # use nano for precision?
  ora_conn.ping()
  n_ms_ping = ( time.perf_counter_ns() - n_start ) / (1000 * 1000 )

  return n_ms_ping  # -- measure 1 ping.. in ms 

# -- -- -- f_rt_1ping defined -- -- --

pp ( ' ----- functions etc. defined, ----- Start of MAIN ----- ' )
pp ( )

ora_conn = ora_logon ()

pp    ( ' ----- ora_logon: done ---- ' )
pp    ()

# check for 1 ping..
pp ( 'single ping  : ', round ( f_rt_1ping ( ora_conn ), 3) , 'ms' )
pp ( ' ' )

# try loop-call of 100 pings..
n_total = 0.0
n_counter = 100
for n_loop in range (1,n_counter):
  n_total += f_rt_1ping ( ora_conn ) 

n_avg = n_total / n_counter
pp ( 'avg of pings : ', round ( n_avg, 3) , ' (over ', n_counter, 'pings)' )

# done this: overhead is in the microseconds, 
# e.g. 1/1000 fraction of the ping time.
n_sec = 2
f_rt_calibrate ( ora_conn, n_sec )

pp    ( ' ----- pings and calibrate done ----- ' )

ora_sess_info ( ora_conn ) 

pp    ()
pp    ( ' ----- session-stats reported ----- ' )

pp    ()
pp    ( ' ----- tst_netw done -----' ) 

