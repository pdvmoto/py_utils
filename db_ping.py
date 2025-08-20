#  tst_ping.py : ping a database 
#  
# requirements: (from blog 16aug?)
#   a ping, report nrRTTs, min/avg/max/stddev.
#   prefer: run infinite when main, run max 100 when in other program.
#   print results and connect-info at bottom ???
#   allow for optional arguments  -i<sec>, allow for -c<count>
#   later: allow for connect-strings ? 
# 
# priority: ping function, with conn + nr-pings, print results, and return avg..
#
# ideas: add count and interval, sar-style 
#   arg1 always the_conn
#   arg2, if present = interval in sec (float)
#   arg3, if present = count, 0=infinite 
#
# todo:
#   args for stand-alone program, CLI version
#   try socket, if listener-alive: then ping, othwise error
#   Bug? !! ping_delay_s causes errors in next cursor when below 1ms ???
# 

# take this one Early.
# from  duration      import *

print ( ' ---- db_ping.py --- ' )

print ( ' ---- db_ping.py first do imports ..--- ' )

import    time
import    string
from      datetime  import  datetime

# local utilities, keep/cp in same directory for now...
# from  duration      import *
from  prefix        import *
from  ora_login     import *

pp    ()
pp    ( ' ----- imports done, next def functions, global, constants ---- ' )
pp    ()

# run ping until contol-C, 
# future version: try to spend ping-time inside DB to equalize time spent
# do a ping, allow to program sleep-time (float, and max_pings, 0=endless )

def f_run_pings ( ora_conn, sleep_s=0.0, n_max_pings=0 ):

  # got errors with 0.0 ??  hence put in 1 microsec
  min_sleep_s = 0.0001

  n_total_ns = 0
  n_counter  = 0
  service_name = ora_conn.service_name
  dsn_descr    = ora_conn.dsn
  result_list = []
  
  if (n_max_pings < 1):
    n_max_pings = ( 1000 * 1000 * 1000)

  # delay has to be at least some microsec, otherwise causes errors???
  if (   sleep_s < min_sleep_s):
    ping_delay_s = min_sleep_s
  else:
    ping_delay_s = sleep_s

  # while True:
  while (n_counter < n_max_pings):

    try: 
      n_start = time.perf_counter_ns()
      ora_conn.ping()
      n_pingtime_ns = time.perf_counter_ns() - n_start 

      result_list.append ( n_pingtime_ns ) 
      n_total_ns        += n_pingtime_ns
      n_counter         += 1

      time.sleep( ping_delay_s )   # somehow, we need a delay ? 

      pp     ( 'service=', service_name, ' seq=', n_counter, ' time=', round ( n_pingtime_ns / (1000 * 1000 ), 3), 'ms' )

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

  # back to 3 decimals, e.g. show up to microseconds
  n_list_min_ms = round ( n_list_min_ms, 3 ) 
  n_list_avg_ms = round ( n_list_avg_ms, 3 ) 
  n_list_max_ms = round ( n_list_max_ms, 3 ) 
  n_list_stddev = round ( n_list_stddev, 3 ) 

  pp ('----', service_name, ' db-ping statisticss: ----' )
  pp ('-- round trip min/avg/max/stddev = ' 
                    + f"{n_list_min_ms:.3f}" + '/'
                    + f"{n_list_avg_ms:.3f}" + '/'
                    + f"{n_list_max_ms:.3f}" + '/'
                    + f"{n_list_stddev:.3f}" + 'ms' )
  pp ('-- from', n_counter, 'pings with delay', ping_delay_s, 'sec')
  pp ('-- dsn =', dsn_descr ) 

  #pp ( '\n verify avg:', n_avg_ms ) # verified, it was correct..
 
  # try catch  errors here... ?
  if ora_conn.is_healthy (): 
    # pp ( ' conn still healthy ' ) 
    # ora_sess_info ( ora_conn ) 
    pass
  else:
    pp ( ' conn is no longer healthy ' ) 
    quit ()

  return n_avg_ms

# -- -- -- run_pings defined -- -- --

# old calibration function..
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

# old function for single-ping
def f_rt_1ping ( ora_conn ):

  n_start = time.perf_counter_ns()        # use nano for precision?
  ora_conn.ping()
  n_ms_ping = ( time.perf_counter_ns() - n_start ) / (1000 * 1000 )

  return n_ms_ping  # -- measure 1 ping.. in ms 

# -- -- -- f_rt_1ping defined -- -- --

pp ( ' ----- functions etc. defined, ----- Start of MAIN ----- ' )
pp ( )

# pick SQL from commandline, if arg1: use it as delay (seconds, float).
if len(sys.argv) == 2:
  delay_s = float ( sys.argv[1] ) 
else:
  delay_s = 1.0001

ora_conn = ora_logon ()

pp    ( ' ----- ora_logon: done ---- ' )
pp    ()

n_pings = 0   # 0 = endless
avg_ms = f_run_pings ( ora_conn, delay_s, n_pings  ) 

pp    ()
pp    ( ' ping result, avg =', avg_ms ) 

# ora_sess_info ( ora_conn ) 
# pp    ()
# pp    ( ' ----- session-stats reported ----- ' )

# ora_time_spent ( ora_conn )

# tmr_report_time () 

pp    ()
pp    ( ' ----- tst_ping done -----' ) 

