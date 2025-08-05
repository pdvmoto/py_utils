#  rt3_ping.py : loop + time heath + ping of coonnection
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

  n_count = 0
  n_start = time.perf_counter()
  while time.perf_counter() - n_start < n_secs:
    n_count += 1
    ora_conn.is_healthy()

  ms_p_health = 1000.0 * n_secs/n_count 

  pp (' ' )
  pp ( 'nr empty health : ', n_count, ' loops/sec: ', n_count/n_secs )
  pp ( 'ms per health   : ', ms_p_health )
  pp (' ' )

  n_count = 0
  n_start = time.perf_counter()
  while time.perf_counter() - n_start < n_secs:
    n_count += 1
    ora_conn.ping()     # The Actual Ping, for n_sec.

  ms_p_ping = 1000.0 * n_secs/n_count 

  pp (' ' )
  pp ( 'nr empty ping : ', n_count, ' loops/sec: ', n_count/n_secs )
  pp ( 'ms per ping   : ', ms_p_ping )
  pp (' ' )

  return  n_secs #  -- -- -- roundtrips...


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
pp    ( ' ----- functions defined ----- ' )
pp    ()


# for n_seconds ..

n_sec = 3 

f_do_pings ( n_sec )

# f_do_sql ( n_sec )

pp    ()
pp    ( ' ----- pings done ----- ' )
pp    ()

# show stats for this connection..
ora_sess_info ( ora_conn )

tmr_report_time () 

pp    ()
pp ( ' ----- roundtrips done -----' ) 

