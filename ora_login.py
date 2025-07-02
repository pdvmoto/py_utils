#
# ora_login.py: , using .env, dotenv, and return the connection.
# another way of isolating the logon cred + avoid typing code
#
# todo: 
# - later: allow un/pwd@host:port\sid to be passed, but prefer dotenv 
# - how many other self-made includes should I depend on ? 
# - include ora_aas: find aas and allow throttling/sleep.
#   if no aas-found, no conn, simply pause bcse no useful work possible
# 

import    os
import    time
import    oracledb
from      dotenv   import load_dotenv

#
# functions in this file:
# ora_logon : use dotenv to get credentials and logon
# ora_sess_info : get some session stats (since logon of sess..)
#
# ora_aas_init  : set startpoint to sample AAS, indication for busy system
# ora_aas_get   : get AAS since init, include nr of CPUs to relate to

# define function to have any arguments, 
# this allow to replace existing functions. 

def ora_logon ( *args ):

  # customize this sql to show connetion info on logon
  sql_show_conn="""
    select 2 as ordr
       , 'version : ' ||  substr ( banner_full, -12) as txt
    from v$version
  UNION ALL
    select 1
       , 'user    : '|| user || ' @ ' || global_name|| ' ' as txt
    FROM global_name     gn
  UNION ALL
    SELECT 3
       , 'prompt  : ' || user
         || ' @ ' ||db.name
         || ' @ '|| SYS_CONTEXT('USERENV','SERVER_HOST')
         || decode  (SYS_CONTEXT('USERENV','SERVER_HOST')
              , '98b6d46dd637',    ' (xe-dev)'
              , '98eac28a59c0',    ' (dckr-23c)'
              , '2c4a51017a44',    ' (dckr-23ai)'
              , ' (-envname-)')
         || ' > '
    FROM    v$database      db
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

  # --- dotenv() specific ------------------------------

  # 
  # verify... dont print this at work.
  print    ( ' ora_login: ' ) 
  print    ( ' ora_login: ' + ora_user + ' / **************** @ ' 
           + ora_server + ' ; ' + ora_port + ' \\ ' + ora_sid )

  # create the actual connection
  ora_conn = oracledb.connect (
      user          = ora_user
    , password      = ora_pwd
    , host          = ora_server
    , port          = ora_port
    , service_name  = ora_sid
  )

  print    ( ' ora_login: --- Connection is: --->' )

  cursor = ora_conn.cursor()
  for row in cursor.execute ( sql_show_conn ):
    print  ( ' ora_login:', row[1] )

  print    ( ' ora_login:  <-- Connection  ---- ' )
  print    ( ' ora_login: ' ) 

  return ora_conn  # ------- logon and return conn object --- 


def ora_sess_info ( the_conn ):
  # 
  # output network and other stats from session 
  # 
  sql_stats = """
    select sn.name, st.value
    --, st.* 
    from v$mystat st
    , v$statname sn
    where st.statistic# = sn.statistic# 
    and (  sn.name like '%roundtrips%'
        or sn.name like 'bytes sent%client'
        or sn.name like 'bytes rece%client'
        or sn.name like '%execute count%'
        or sn.name like 'user calls'
        or sn.name like 'user commits'
        or sn.name like 'user rollbacks'
        or sn.name like 'consistent gets'
        or sn.name like 'db block gets'
        or sn.name like 'opened cursors current'
        or sn.name like 'opened cursors curr%'
        or sn.name like '%sorts%'
        or sn.name like '%physical reads'
        )
      order by sn.name 
  """

  print ( ' ora_sess_info: Report out Session Stats ' ) 

  cur_stats = the_conn.cursor()
  for row in cur_stats.execute ( sql_stats ):
    # p   ( ' stats : ', row[1], ' ', row[0] )
    print   ( ' ora_sess_info: ', f"{row[1]:8.0f}  {row[0]}"   )

  return 0 # -- -- -- -- ora_sess_info


# -- --  ora_aas -- -- 

# define the global ora_aas variables and functions
ora_aas_prev_dbtime_ms = 0    # last measured valie, 0 = not initialized yet
ora_aas_prev_dt_epoch  = 0    # epoch in sec when last db_time was queried

ora_aas_query = """ 
  select 
    value                                                   as db_time_ms
  , (sysdate - TO_DATE('1970-01-01', 'YYYY-MM-DD')) * 86400 as epoch_sec
  from v$sysstat
  where name = 'DB time'
"""

# check for AAS, determine if pause needed, return ms-duration 

def ora_aas_chk ( conn_obj):

  start_ms = time.time() * 1000

  global ora_aas_prev_dbtime_ms
  global ora_aas_prev_epoch_s

  load_dotenv()

  # get env ... (what if not in env?)
  ora_aas_threshold_pct    = float ( str ( os.getenv ( 'ORA_AAS_THRESHOLD_PCT' ) ) )
  ora_aas_pause_sec        = int   ( str ( os.getenv ( 'ORA_AAS_PAUSE_SEC'     ) ) )

  print ( ' ora_aas : from env, thrshld: ', ora_aas_threshold_pct, ', ora_aas_pause: ', ora_aas_pause_sec )

  # get the values from database..
  cur_aas = conn_obj.cursor()
  for row in cur_aas.execute ( ora_aas_query ):
    
    # print   ( ' ora_aas : info found epoch and dbtime: ', f"{row[1]}  {row[0]}"   )
    # should only be 1 row...
 
    dbtime_ms = int ( row[0] )
    epoch_s   = int ( row[1] )
  
  # end for-cursor, should only be 1

  print ( ' ora_aas : dbtime: ', dbtime_ms, ', epoch: ', epoch_s )

  # when not ini, just pause
  # else, if already init: determine if pause wanted..

  if ora_aas_prev_dbtime_ms == 0:

    print ( ' ora_aas: initiated and doing pause ', ora_aas_pause_sec, ' sec.' ) 
    time.sleep ( ora_aas_pause_sec )  

  else: # no init, but

    # calculate aas percentage (explicit calcs, allow debug)
    delta_dbtime_ms = dbtime_ms - ora_aas_prev_dbtime_ms
    delta_epoch_s   = epoch_s   - ora_aas_prev_epoch_s
    aas_pct = ( 100 * 
         ( delta_dbtime_ms      ) 
       / ( delta_epoch_s * 1000 ) 
     )

    print ( ' ora_aas : delta_dbtime_ms =', delta_dbtime_ms )
    print ( ' ora_aas : delta_epoch_s   =', delta_epoch_s )
    print ( ' ora_aas : aas_pct         =', aas_pct )

    if aas_pct > ora_aas_threshold_pct:

      print ( ' ora_aas : need pause - yes ' )
      time.sleep ( ora_aas_pause_sec ) 

    else:

      print ( ' ora_aas : dont need pause  - no' ) 

    # endif, needed pause or not

  # end if-else, inti or check 

  # save the prev values
  ora_aas_prev_dbtime_ms = dbtime_ms
  ora_aas_prev_epoch_s   = epoch_s
  
  end_ms = time.time() * 1000
  duration_ms = end_ms - start_ms

  print ( ' ora_aas : done, return duration: ', duration_ms )

  return duration_ms

# ---- some  test code below... ---- 

sql_test = """
  select object_type, count (*) 
    from user_objects 
   group by object_type  
"""

if __name__ == '__main__':

  print ()
  print ( ' ---- testing ora_logon function ----- ' )
  print ()

  ora_conn = ora_logon ()

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

  time.sleep( 10 )
  ora_aas_chk ( ora_conn )

  print ()
  print ( ' ---- ora_logon: check the stats, for current sesion ---- ' ) 
  print ()

  ora_sess_info ( ora_conn )

  print ()
  print ( ' ---- ora_sess_info: tested with current session ---- ' ) 
  print ()

