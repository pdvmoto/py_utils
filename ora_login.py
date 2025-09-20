#
# ora_login.py: , using .env, dotenv, and return the connection.
#
# another way of isolating the logon cred + avoid typing code
# plus to isolate some oracle-related code: session info, timing-data..
# Tested: v19.0 .. v23.9
#
# grants needed:  (can we get round these... ? )
#   grant select on v_$mystat, v_$version, v_$statname, v_$sess_time_model to ... 
#   grant select on v_$sysstat, v_$parameter to ... 
# 
# functions included
#
#   ora_logon ( *args )        - Actually picks up credentials from dotenv : .env
#   ora_get_mod   ( conn,prog) - Get module_mame for conn, format "prog:(sid,serial)"
#   ora_sess_info ( the_conn ) - reports on "totals" from v$mystat and v$sess_time_model
#   ora_sess_inf2 ( the_conn ) - idem, but difference since previous call
#   ora_sess_hist ( the_conn ) - stmnts from v$sql_history (if available...)
#
#   ora_aas_chk ( the_conn )   - check how busy RDBMS is, do pause-sleep if necessary
#
#   ora_rt_1ping ( the_conn )  - do 1 ping over the connection, report back ms (milliseconds)
#   ora_time_spent ( the_conn )  - report time spent by program: python + RDBMS + Network + idle
#
#
# Dependencies:
#   duration.py : timing info
#   prefix.py   : pp for timed-print
#
# todo: 
# - timing,.. should we load duration.py at the very top ? => test!
# - later: allow un/pwd@host:port\sid to be passed, but prefer dotenv 
# - help text in case dot-env file is not found !!!
# - self-made include-files: duration, prefix,.. really ?
# - logon + sess_info: avoid dependency on v$ ... hmmm ??
# - aas : dflt pause on (SQL)error, use cursor.parse to test..
# - include ora_aas: find aas and allow throttling/sleep.
#   if no aas-found, no conn, simply pause bcse no useful work possible
# 
# info: unless prefetch is increased,... 
#   Apparently connect takes 2 round trips.
#   the "show prompt" takes 2 round trips
#   and ora_sess_info also takes 2 round trips
#

import    os
import    time
import    oracledb
from      dotenv   import load_dotenv

# we use those..., 

from prefix     import *
from duration   import *


# -- -- -- Constants, notably SQL -- -- -- 

# name to set module..
g_ora_module = 'ora_login_selftest'

# to get statistics from DB, adjust per demo..
sql_stats2 = """
  select /* s2 stats */ sn.name, st.value
  -- , st.*
  from v$mystat st
  , v$statname sn
  where st.statistic# = sn.statistic# 
  and (  sn.name like '%roundtrips%client%'
      -- or sn.name like 'bytes sent%client'
      -- or sn.name like 'bytes rece%client'
         or sn.name like '%execute count%'
         or sn.name like 'user calls'
      -- or sn.name like 'user commits'
      -- or sn.name like 'user rollbacks'
      -- or sn.name like 'consistent gets'
      -- or sn.name like 'db block gets'
      -- or sn.name like 'opened cursors current'
      -- or sn.name like 'opened cursors curr%'
      -- or sn.name like '%sorts%'
      -- or sn.name like '%physical reads'
         or sn.name like '%arse count (hard%'
         or sn.name like 'DB time'
      )
  UNION ALL
    select ' ~ ', 0 from dual where 1=0
  UNION ALL
    select ' ' || stm.stat_name || ' (micro-sec)'
         , stm.value
    from v$sess_time_model  stm
    where  1=1
      and stm.sid =  sys_context('userenv', 'sid')
      and (     stm.stat_name like 'DB time'
          -- or stm.stat_name like 'DB CPU'
          -- or stm.stat_name like 'sql execu%'
          -- or stm.stat_name like 'PL/SQL execu%'
          )
    order by 1
"""

# -- -- -- functions... -- -- -- 

def ora_get_mod ( ora_conn, prog_name='a_python_prog' ):
           
  # get the module_id (string) for this connection: 
  # others will use it to set-module, and to query for session-info.
  # module_string should be max 48, and unique..
  # for the moment: "mod_(sid,serial#)' (including the parentheses) 
  # so typical would be : "mod_(42,2345)"

  # set module to "program:(sid,serial), to allow finding stmnts later
  module_id = str ( prog_name + ':(' + str ( ora_conn.session_id ).strip()
                  + ','       + str ( ora_conn.serial_num ).strip() + ')' )
                
  return module_id

def ora_logon ( *args ):

  # customize this sql to show connetion info on logon
  # note: re-worked to avoid ORA-00942 or priv-errors
  sql_show_conn="""
    select /* get conn-info */ 2 as ordr
       , 'version : ' ||  substr ( banner_full, -12) as txt
    from v$version
  UNION ALL
    select 1
       , 'user    : '|| user || ' @ ' || global_name|| ' ' as txt
    FROM global_name     gn
  UNION ALL
    SELECT 3
       , 'prompt  : ' || user
         || ' @ '  || global_name           -- ||db.name
         -- || ' @ ' || REGEXP_SUBSTR(banner_full, 'version [^ ]+', 1, 1, 'i') 
         -- || ' @ '|| SYS_CONTEXT('USERENV','SERVER_HOST')
         || decode  (SYS_CONTEXT('USERENV','SERVER_HOST')
              , '98b6d46dd637',    ' (xe-dev)'
              , '98eac28a59c0',    ' (dckr-23c)'
              , '2c4a51017a44',       ' (dckr-23ai)'
              , 'oracle-19c-vagrant', ' (test19c)'
              , 'ora19tst',           ' (tst19c_ORCL)'
              , ' (-envname-)')
         || ' > '
    FROM   global_name  -- v$version      ver
  order by 1
  """

  # --- dotenv() specific --- ----------------------------
  # --- but feel free to code your own "credentials" here.

  load_dotenv()

  # get + verify..
  ora_user    = os.getenv ( 'ORA_USER' )
  ora_pwd     = os.getenv ( 'ORA_PWD' )
  ora_server  = os.getenv ( 'ORA_SERVER' )
  ora_port    = os.getenv ( 'ORA_PORT' )
  ora_sid     = os.getenv ( 'ORA_SID' )

  # bonus: arraysize and prefetch, if available
  ora_arraysize     = os.getenv ( 'ORA_ARRAYSIZE' )
  ora_prefetchrows  = os.getenv ( 'ORA_PREFETCHROWS' )
  
  # --- dotenv() specific ------------------------------

  # 
  # verify... dont print this at work.
  print    ( ' ora_login: ' ) 
  print    ( ' ora_login: ' + ora_user + ' / **************** @ ' 
           + ora_server + ' ; ' + ora_port + ' / ' + ora_sid )

  # create the actual connection
  ora_conn = oracledb.connect (
      user          = ora_user
    , password      = ora_pwd
    , host          = ora_server
    , port          = ora_port
    , service_name  = ora_sid
  )

  print    ( ' ora_login: ----- Connection is: --->' )
  
  cursor = ora_conn.cursor()
  cursor.prefetchrows = 10      # set prefetch to limit round trips
  for row in cursor.execute ( sql_show_conn ):
    print  ( ' ora_login:   ', row[1] )

  print    ( ' ora_login: <---- Connection  ---- ' )

  # adjust array and prefetch if found via Dot-Env..

  if (ora_arraysize is not  None ):
    oracledb.defaults.arraysize    = int ( ora_arraysize )
    print ( ' ora_login: Modified Arraysize    = ', ora_arraysize )

  if ( ora_prefetchrows is not None ):
    oracledb.defaults.prefetchrows    = int ( ora_prefetchrows ) 
    print ( ' ora_login: Modified Prefetchrows = ', ora_prefetchrows )

  print   ( ' ora_login: ' ) 

  return ora_conn  # ------- logon and return conn object --- 


def ora_sess_info ( the_conn ):
  # 
  # output network and other stats from session 
  #
  # note the overhead of this call: 
  #  1 round trip (optimized prefetch )
  #  1 user call 
  #  1 execute  
  #  1 sort (memory)
  #  other overhead depends on how many rows..
  # 
  sql_stats = """
    select sn.name, st.value
    -- , st.*
    from v$mystat st
    , v$statname sn
    where st.statistic# = sn.statistic# 
    and (     sn.name like '%roundtrips%client%'
        -- or sn.name like 'bytes sent%client'
        -- or sn.name like 'bytes rece%client'
           or sn.name like '%execute count%'
           or sn.name like 'user calls'
        --or sn.name like 'user commits'
        --or sn.name like 'user rollbacks'
        -- or sn.name like 'consistent gets'
        -- or sn.name like 'db block gets'
        -- or sn.name like 'opened cursors current'
        -- or sn.name like 'opened cursors curr%'
        -- or sn.name like '%sorts%'
        -- or sn.name like '%physical reads'
        or sn.name like '%arse count (hard%'
        or sn.name like 'DB time'
        )
    UNION ALL
    select ' ~ ', 0 from dual
    union all
    select ' ' || stm.stat_name || ' (micro-sec)'
         , stm.value
    from v$sess_time_model  stm
    where stm.sid =  sys_context('userenv', 'sid')
      and (  stm.stat_name like 'DB time'
          or stm.stat_name like 'DB CPU'
          or stm.stat_name like 'sql execu%'
          or stm.stat_name like 'PL/SQL execu%'
          )
    order by 1
    """

  print ( ' ora_sess_info: Session Stats, '
          , '(sid, serial)= (', the_conn.session_id, ',', the_conn.serial_num, ')'
        )
  print ( ' ora_sess_info:     Value  Stat name \n ora_sess_info:   -------- -------------' ) 

  cur_stats = the_conn.cursor()
  cur_stats.prefetchrows = 30      # set to limit round trips

  # optional: parse to test the cursor.. return on err..j
  # but only when needed: it is 1 extra RT
  # cur_stats.parse ( sql_stats2 )  

  for row in cur_stats.execute ( sql_stats2 ):
    # print ( ' stats : ', row[1], ' ', row[0] )
    print   ( ' ora_sess_info: ', f"{row[1]:8.0f}  {row[0]}"   )

  return 0 # -- -- -- -- ora_sess_info


# -- -- -- ora_sess_inf2 : the advanced version.. -- -- -- 

g_sess_info_dict = {}           # keep global for re-use over calls

def ora_sess_inf2 ( the_conn ):
  # 
  # output network and other stats from session 
  #
  # note the overhead of this call: 
  #  x round trip (optimized prefetch )
  #  x user call 
  #  x execute  
  #  x sort (memory)
  #  other overhead depends on how many rows..
  # 

  global g_sess_info_dict         # keep info over calls, data from previous call
  sess_info_now = {}              # local, recent data.

  print ( ' ora_sess_inf2:   -- -- Session Stats since previous call -- -- ')
  print ( ' ora_sess_inf2:     Value  Stat name \n ora_sess_info:   -------- -------------' ) 

  sess_info_now = {}
  cur_stats = the_conn.cursor()
  cur_stats.prefetchrows = 30      # set array to limit round trips
  for row in cur_stats.execute ( sql_stats2 ):

    # print   ( ' ora_sess_inf2: ', f"{row[1]:10.0f}  {row[0]}"   )
    # add to dict..for next  time
    sess_info_now [ row[0] ] = row[1]

  # debug stuff.
  # print ( ' ora_sess_inf2: ', len ( sess_info_now ), ' new items' ) 
  # print ( ' ora_sess_inf2: ', len ( g_sess_info_dict ), ' existing items' ) 
  
  # if prev version exists: show diffs
  if ( len ( g_sess_info_dict ) > 0 ):      # if global-(previous) data available, display diffs

    for stat_key in g_sess_info_dict: 
      diff = sess_info_now [ stat_key ] - g_sess_info_dict [ stat_key ] 
      print   ( ' ora_sess_inf2: ', f"{diff:10.0f}  {stat_key}"   )
 
  else:                                     # initial call.. display now-values 

    for stat_key in sess_info_now: 
      print   ( ' ora_sess_inf2: ', f"{ sess_info_now [ stat_key ]:10.0f}  {stat_key}"   )

  # keep dict for next call
  g_sess_info_dict = dict ( sess_info_now )

  return 0 # -- -- -- -- ora_sess_inf2

#
# try finding SQL-history for the session
# consider: overriding pp ( )
#
def ora_sess_hist ( the_conn ):

  # local override..
  def pp ( *args ):
    print ( ' sql_hist: ', *args ) 
    return 0

  n_retval = 0

  sql_hist_select="""
    select /* vsql_hist ******  sql_id
    --, to_char ( h.sql_exec_start, 'HH24:MI:SS' ) as start_tm
      , h.elapsed_time ela_us
    --, h.cpu_time cpu_us, h.buffer_gets buff_g
      , replace ( substr ( h.sql_text, 1, 70 ), chr(10), '|' ) sql_txt
      , h.key ***/
     rpad ( h.sql_id, 14 )
       ||  to_char ( count (*)               , '999999999' )
       ||  to_char (   sum ( h.elapsed_time ), '999999999' )
       ||  to_char (   sum ( h.cpu_time )    , '999999999' )  || ' '
       ||  replace ( substr ( h.sql_text, 1, 50 ), chr(10), ' ' ) || '...'
    from v$sql_history h
    where 1=1
      and h.sid = SYS_CONTEXT ('USERENV', 'SID')
    group by h.sql_id, h.sql_text
    order by  sum (h.elapsed_time)
  """
  # retun: mulitple columnms.. later version: return just 1 varchar, is easier

  sql_has_history ="""
    select /* check params */ 
      decode ( p.value, 'TRUE', 1, 0 ) as result
    from v$version v
       , v$parameter p
    where 1=1
    and v.banner like '%23ai%'
    and p.name = 'sql_history_enabled'
  """
  # return 1 number, or no rows at all.

  # pp ( )
  # pp ( 'start of ora_sql_hist, try retrieving SQL-stmnts for this program-run' )

  # check only if version is 23, and only if parameter is set..

  cur_hist = the_conn.cursor ()
  cur_hist.execute ( sql_has_history )
  row = cur_hist.fetchone ()

  if (  ( cur_hist.rowcount <  1 ) 
     or ( int( row[0] )     != 1 )
    ):
    pp ( ' ' ) 
    pp ( 'sql_history not available, check Version == 23ai, and SQL_HISTORY_ENABLED = True' )
    pp ( ' ' ) 
    return 0 

  #if int( row[0] ) != 1:
  #  pp ( ' ' ) 
  #  pp ( 'sql_history not available, check Version == 23ai, and SQL_HISTORY_ENABLED = True' )
  #  pp ( ' ' ) 
  #  return 0 

  # if we get here: we can look for sql_history...

  pp    ( ' ' )
  pp    ( '... SQL history, ordered by ela_us ...' )
  pp    ( ' ' )
  pp    ( 'row  sql_id          exe_count    ela_us   cpu_us      SQL ...' )
  pp    ( '---- -------------- ---------- --------- -------- -------- ... ' )

  cursor = the_conn.cursor()
  for row in cursor.execute ( sql_hist_select ):
    pp   ( f"{cursor.rowcount:4d}", row[0] )

  pp ()

  return cursor.rowcount 


def ora_module_sqlarea ( the_conn, the_module='%' ):

  # pick the stmnts for the current session-module form sqlarea
  # this assues the module_name was set for the connection using ora_get_module
  # alternatively it can list all of the SQL

  def pp ( *args ):
    print ( 'ora_module_sql:', *args ) 
    return 0

  n_maxrows = 100 

  sql_get_module_sqlarea="""
    select /* get sqlarea module */ s.result_txt from 
    ( select 
      /*** s.sql_id
      , s.executions                            as nr_exe
      , s.elapsed_time                          as ela_us
      , s.cpu_time                              as cpu_us
      --, s.elapsed_time / s.executions           as us_p_exe
      , substr ( s.sql_text, 1, 60 )            as sql_txt
      ***/
      '' 
       || to_char (   sum ( s.elapsed_time ), '9999999999' )
       || to_char (   sum ( s.executions )  , '999999999' )      || '  ' 
       || rpad ( s.sql_id, 14 ) || ' '
       || replace ( substr ( s.sql_text, 1, 60 ), chr(10), ' ' ) || '...' as result_txt
       , s.elapsed_time                                                   as ela_us
      from v$sqlarea s
      where 1=1  
        and s.module like :b_module || '%' 
      group by s.sql_id, s.sql_text, s.elapsed_time
      order by s.elapsed_time desc
      FETCH FIRST :b_maxrows ROWS ONLY
    ) s 
  order by s.ela_us 
  """
  # just 2 binvar: the moudule_name, and maxrows

  # why do we need to assign paramteer to local ???
  like_module = the_module

  pp    ( ' ' )
  pp    ( '... SQL found for module: [', like_module + '% ]' )
  pp    ( ' ' )
  pp    ( 'row  ela_us      exe_count  sql_id         SQL ...' )
  pp    ( '---- ----------- ---------  -------------  ---------- - ... ' )

  cur_sqlarea = the_conn.cursor ()
  for row in cur_sqlarea.execute ( sql_get_module_sqlarea
                                 ,  b_module = like_module
                                 , b_maxrows = n_maxrows 
  ):
    pp   ( f"{cur_sqlarea.rowcount:4d}", row[0] )

  n_retval = cur_sqlarea.rowcount 

  pp ()
  pp ( 'module: [', like_module, ' ], found:', n_retval, 'stmnts.' )
  if (n_retval == 100):
    pp ( '(list is limited to max 100 distinct stmnts)')
  pp ()


  return n_retval

  # ----- end of ora_module_sqlarea:print sqlarea for session -----

def  ora_sqlarea ( the_conn ):

  # stmnts from SQLAREA, orderded by Elapsed time..
  # fine tune by eliminating SYS, 

  def pp ( *args ):
    print ( 'ora_sqlarea:', *args ) 
    return 0

  sql_get_sqlarea="""
    select * from ( 
      select /* get sqlarea module */ 
      /*** s.sql_id
      , s.executions                            as nr_exe
      , s.elapsed_time                          as ela_us
      , s.cpu_time                              as cpu_us
      --, s.elapsed_time / s.executions           as us_p_exe
      , substr ( s.sql_text, 1, 60 )            as sql_txt
      ***/
      rpad ( s.sql_id, 14 )
             ||  to_char (   sum (s.executions )   ,           '99999999' )
             ||  to_char (   sum ( s.elapsed_time / ( 1000) ), '99999999' ) || ' ' 
             ||  replace ( substr ( s.sql_text, 1, 60 ), chr(10), ' ' ) || '...'
      , s.elapsed_time                          as ela_us
      from v$sql s
      where 1=1 
        and parsing_user_id > 0  -- skip SYS
      group by s.sql_id, s.sql_text, s.elapsed_time
      order by s.elapsed_time desc 
      FETCH FIRST 10 ROWS ONLY
    )
  order by ela_us  -- now show highest ela at bottom
  """
  # no binvar on this one

  pp    ( ' ' )
  pp    ( '... SQL-area, orederd by elapsed_ms  for DB-instance or PDB:', the_conn.service_name )
  pp    ( ' ' )
  pp    ( 'row  sql_id          exe_cnt   ela_ms SQL ...' )
  pp    ( '---- -------------- -------- -------- -------- ... ' )

  cur_sqlarea = the_conn.cursor ()
  for row in cur_sqlarea.execute ( sql_get_sqlarea ):
    pp   ( f"{cur_sqlarea.rowcount:4d}", row[0] )

  pp ()

  n_retval = cur_sqlarea.rowcount 
  return n_retval

  # ----- end of ora_sqlarea: sqlarea for instancw -----

# -- --  ora_aas -- -- 
 
# ora_aas_chk ( conn): allow python to sleep when oracle is too busy.
#
# note: 
#   needs values in dot-env
#   units are mostly in seconds. with sub-second intervals, the overhead wil be too high!
# 

# the global g_ora_aas variables, they persist over calls
g_ora_aas_prev_dbtime_ms = 0    # last measured value, 0 = not initialized yet
g_ora_aas_prev_dt_epoch  = 0    # epoch in sec when last db_time was queried

# the query to get data for ora_aas:
sql_ora_aas_query = """ 
  select 
    s.value                                                   as db_time_ms
  , (sysdate - TO_DATE('1970-01-01', 'YYYY-MM-DD')) * 86400   as epoch_sec
  , p.value                                                   as cpu_count
  from v$sysstat   s
     , v$parameter p
  where s.name = 'DB time'
    and p.name = 'cpu_count'
"""

# check for AAS, determine if pause needed, return ms-duration 

def ora_aas_chk ( conn_obj ):

  start_ms = time.time() * 1000

  global g_ora_aas_prev_dbtime_ms
  global g_ora_aas_prev_epoch_s

  # always check the latest parameters from .env
  load_dotenv()

  # get env ... (what if not in env?)
  ora_aas_threshold_pct    = float ( str ( os.getenv ( 'ORA_AAS_THRESHOLD_PCT' ) ) )
  ora_aas_pause_sec        = int   ( str ( os.getenv ( 'ORA_AAS_PAUSE_SEC'     ) ) )

  print (   'ora_aas: threshold_pct =', ora_aas_threshold_pct
        , '\nora_aas: pause_sec     =', ora_aas_pause_sec )

  # get the values from the database at conn_obj..
  cur_aas = conn_obj.cursor()
  for row in cur_aas.execute ( sql_ora_aas_query ):
    
    # print   ( 'ora_aas: info found epoch and dbtime: ', f"{row[1]}  {row[0]}, cpu_count: {row[2]}"   )
    # should only be 1 row...
 
    dbtime_ms = int ( row[0] )
    epoch_s   = int ( row[1] )
    cpu_count = int ( row[2] )
  
  # end for-cursor, should only be 1

  # print ( 'ora_aas: fetched values dbtime: ', dbtime_ms, ', epoch: ', epoch_s, ', cpu_count: ', cpu_count )

  # when not yet ini, consider pause, or do nothing..
  # else, if already init: determine if pause wanted..

  if g_ora_aas_prev_dbtime_ms == 0:

    # print ( ' ora_aas: initiated, pause_sec set to ', ora_aas_pause_sec, ' sec.' ) 
    # no need... time.sleep ( ora_aas_pause_sec )  
    pass

  else: # init was done already, now check deltas

    # calculate aas percentage (explicit calcs, allow debug)
    delta_dbtime_ms = dbtime_ms - g_ora_aas_prev_dbtime_ms
    delta_epoch_s   = epoch_s   - g_ora_aas_prev_epoch_s
    aas_pct = ( 100 * 
         ( delta_dbtime_ms      ) 
       / ( delta_epoch_s * 1000 ) 
     )
    pct_busy = aas_pct / cpu_count

    print ( 'ora_aas: delta_dbtime_ms =', delta_dbtime_ms )
    print ( 'ora_aas: delta_epoch_s   =', delta_epoch_s )
    print ( 'ora_aas: aas_pct         =', aas_pct )
    print ( 'ora_aas: cpu_count       =', cpu_count )
    print ( 'ora_aas: pct_busy        =', pct_busy )

    if pct_busy > ora_aas_threshold_pct:

      print ( 'ora_aas: pause         => yes ' )
      time.sleep ( ora_aas_pause_sec ) 

    else:

      print ( 'ora_aas: pause         => no' ) 
      pass

    # endif, needed pause or not

  # end if-else, inti or check 

  # save the prev values
  g_ora_aas_prev_dbtime_ms = dbtime_ms
  g_ora_aas_prev_epoch_s   = epoch_s
  
  end_ms = time.time() * 1000
  duration_ms = round ( (end_ms - start_ms), 3)

  print ( 'ora_aas: done, duration was: ', duration_ms, ' ms.' )

  return duration_ms  # -- end of function ora_aas_chk, return duration

# 
# ping function to sample RTT, return milliseconds (float)
def ora_rt_1ping ( ora_conn ):

  n_start = time.perf_counter_ns()        # use nano for precision?
  ora_conn.ping()
  n_ms_ping = ( time.perf_counter_ns() - n_start ) / (1000 * 1000 )

  return n_ms_ping  # -- measure 1 ping.. in ms

# -- -- -- ora_rt_1ping defined -- -- --


# pp (' ------ define constants for ora_time_spent (move this code? ) ------ ')
# pp ()

# the sql can be defined outside...
# get DB-time (cc and microsec), and RTs...
sql_timers="""
  select st_rt.value     as nr_rts 
  ,      st_cs.value     as db_time_cs
  ,      st_tm.value  as db_time_micro
  from v$mystat   st_rt
     , v$mystat   st_cs
     , v$sess_time_model st_tm
  where 1=1
  and st_rt.statistic#   = ( select statistic# from v$statname where name like '%roundtrips%client%' )
  and st_cs.statistic#   = ( select statistic# from v$statname where name like 'DB time' )
  and st_tm.sid       =  sys_context('userenv', 'sid')
  and st_tm.stat_name = 'DB time'
"""
# note: 3 return values, integers, can use row[0], row[1], row[2]..

# -- -- -- a function to try and report Where Time Was Spent... -- -- --

def ora_time_spent ( ora_conn ):

  def pp ( *args ):
    print ( ' ora_time_spent:', *args )
    return 0

  pp ()
  pp ('Collecting time-data: nr-RTs, ping-time, process-time and elapsed time..' )

  # sample the ping-time..  try loop-call of n pings..
  n_counter = 5
  sleep_s   = 0.1
  ping_ms   = 0.0
  total_ms  = 0.0

  for n_loop in range (1,n_counter+1):
    ping_ms     = ora_rt_1ping ( ora_conn )
    total_ms   += ping_ms

    # optional sleep-time, similar to -i<sec>..
    # pp ('ping DB: ', ora_conn.service_name, ' seq=', n_loop, ' RTT=', ping_ms )
    time.sleep( sleep_s )                             # should be configurable, -i<n>
    # tmr_spin ( sleep_s )                            # can spin to avoid "unaccountable" 

  avg_ping_ms = total_ms / n_counter

  # pp ()
  # pp ( 'RTT - avg of pings : ', round ( avg_ping_ms, 3) , 'ms (over ', n_counter, 'pings)' )

  # now get DB-time (cc and microsec), and RTs...

  cur_timers = ora_conn.cursor () 
  for row in cur_timers.execute ( sql_timers ):
    n_rts           = row[0]
    db_time_cs      = row[1]
    db_time_micro   = row[2]
    # pp ( 'DB - statistics: nrRTs=', n_rts, ' DB_time_cs=', db_time_cs, 'DB_time_micro=', db_time_micro )

  # the process and elapsed time in pythyon:
  # note: put this code as late as possible..
  # note: can eliminate some lines, but keep them for clarity
  nano_to_sec    = int ( 1000 * 1000 * 1000 )
  app_process_ns = time.process_time_ns ()                      # this seems to start at 0
  ela_time_ns    = time.perf_counter_ns() - g_durat_proctim_ns  # perf_counter =~ epoch ? 

  # wrap it up: network time, total time..

  app_process_s = round ( app_process_ns / nano_to_sec   , 6) 
  db_time_s     = round ( db_time_micro / (1000*1000)    , 6) 
  netw_time_s   = round ( n_rts * avg_ping_ms / 1000     , 6)
  total_time_s  = round ( ela_time_ns / nano_to_sec      , 6)

  idle_time_s  = round ( (ela_time_ns / nano_to_sec) 
                        - app_process_s
                        - db_time_s
                        - netw_time_s                    , 6 )
  pp ( ' ' )
  pp ( ' App time (busy)  :' , f"{app_process_s:8.3f}", 'sec, = user + sys' )
  pp ( ' DB time          :' , f"{db_time_s:8.3f}"    , 'sec, via sess_time_model' )  
  pp ( ' Network time     :' , f"{netw_time_s:8.3f}"  , 'sec, (', n_rts, 'RTs x', round ( avg_ping_ms, 3), 'ms)' )  
  pp ( ' Idle (wait)time? :' , f"{idle_time_s:8.3f}"  , 'sec, (e.g. RTT or keyb-input, ...)' )
  pp ( '------------------  ----------' )
  pp ( 'Total time        :' , f"{total_time_s:8.3f}" , 'sec (from time.perf_counter_ns)' )


  return 0    # -- -- -- end ora_time_spent () -- -- -- 
              # what would be a good return-value  ?

# ---- some  test code below... ---- 

sql_test = """
  select /* ora_login: Selftest */ object_type, count (*) 
    from user_objects 
   group by object_type  
"""

if __name__ == '__main__':

  print ()
  print ( ' ---- testing ora_logon function ----- ' )
  print ()

  ora_conn = ora_logon ()

  # set module to ID program and session
  module_name = ora_get_mod ( ora_conn, g_ora_module ) 
  ora_conn.module = module_name 

  print ()
  print ( ' ---- if connected, init ora_aas ----- ' )
  print ()

  ora_aas_chk ( ora_conn )

  print ()
  print ( ' ---- if connected, test a query ----- ' )
  print ()

  cur_logon = ora_conn.cursor ()
  for row in cur_logon.execute ( sql_test ):
    print ( ' ora_logon:', row ) 
  
  print ()
  print ( ' ---- ora_logon: tested count *  user_objects, do 1 more aas ---- ' ) 
  print ()

  n_sec = 2

  print ()
  print ( ' ---- ora_logon: re-check ora_aas in ', n_sec, 'sec, using while ---- ' ) 
  print ()

  time.sleep( n_sec )

  while ora_aas_chk ( ora_conn ) > 1000:  # sleep and only release when AAS Below Threshold.
    pass

  print ()
  print ( ' ---- ora_logon: check the stats, for current sesion ---- ' ) 

  ora_sess_info ( ora_conn )

  print ()
  print ( ' ---- ora_logon: re-check the stats, measure overhead of sess_info ---- ' ) 

  ora_sess_info ( ora_conn )

  print ()
  print ( ' ---- ora_logon: test the DICT-version of seession_info ---- ' ) 

  ora_sess_inf2 ( ora_conn )
  print ()
  print ( ' single ping: ', ora_rt_1ping ( ora_conn ), 'ms' ) 
  print ()
  ora_sess_inf2 ( ora_conn )

  print ()
  print ( ' ---- almost final check: report history (23ai only)' )

  ora_sess_hist ( ora_conn ) 

  print ()
  print ( ' ---- SESSION, check: report V$SQLAREA, precisely this session-only... ' )

  # suffix the global by (sid,serial), for more precise select-like
  module_name = ora_get_mod ( ora_conn, g_ora_module )
  ora_module_sqlarea ( ora_conn, module_name ) 

  print ()
  print ( ' ---- MODULE check: report V$SQLAREA, any SQL by this module... ' )

  # just list anything like g_ora_module%
  ora_module_sqlarea ( ora_conn, g_ora_module ) 

  print ()
  print ( ' ---- INSTANCE check: report V$SQLAREA, use module=% ... ' )
  ora_module_sqlarea ( ora_conn ) 

  # all of SQLAREA

  print ( ' ---- INSTANCE check: report V$SQLAREA, old function  ... ' )
  ora_sqlarea ( ora_conn ) 

  print ()
  print ( ' ---- report time spent...' )

  ora_time_spent ( ora_conn ) 

  # tmr_report_time()

  print ('Note: timings not accurately reported on small time-scale of the test.')
  print ()
  print ( ' ---- ora_login.py: various functions tested with current session ---- ' ) 
  print ()

