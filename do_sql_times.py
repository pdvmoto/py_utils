#
# import duration as early as possible, to set start-timers.

from      duration      import *

#
# do_sql_times.py : enter a query, or use $1, and run it. 
#                   this version prints results and timing data
#
# background:
#   clone of do_sql.py: run a g neric query.. 
#   This verions is altered to "Measure" timings, and v$mystats.
#
# depends on:
#   duration.py
#   prefix.py
#   ora_login.py
#   dotenv utility, and the file .env
#
# Stern Warning: 
#   This tool uses "dynamic SQL", 
#   and is Thus susceptible to SQL-Injections.
#   (hey, this tool IS exactly that: SQL-Injection,
#    Deal With It. ;-)
#
# notice:
# - no COMMIT, hence any DML will fail bcse no auto-commit, but..
# - any DDL will Succeed! => big risk.
#
# todo: specific for timer-version
#   - ...
#
# todo (from generic do_sql.py) :
# - use try-except to handle and report errors
# - consider using credentials, conn_name, from SQLcl
# - allow for a pager, and space / enter / nr to continue (never if arg-1 provided)
# - allow silent or scripted run: dont require keyboard input (+/- done)
# - allow Stealth: only output row-lists, no other output, allow csv-spooling
# - devise some automated testing, and test more extensively
# - Graceful Exit on SQL-error (gently report ORA-00942 etc..).
# - enable use with other drivers, databases as well
# - remove need for quotes around arg[1] (nah...)
# - provide for -h --h, --help..
# - report program-stats (time..) and sql-stats (make it optional...)
# - provide multi-line input until ; or empty is given.
# - also output to file e.g. a.out ( but pipe-tee a.out works fine)
# - run sql-stmnts from file: -f filename ( pipe-in works, but only for 1 stmnt )
# - more on vector processing (how would we like to see....)
# - catch Control-D, -C, \q...
# - lots more, but not prio atm
#

print ( ' ' ) 
print ( '--------- do_sql_times.py: enter manual queries, test... ---------- ' )
print ( ' ' ) 

import    os
import    sys
import    array

import    oracledb 

print ( '--------- generic imports done  -------------- ' )
print ( ' ' )

from      prefix        import *
from      ora_login     import *

pp    ( ' ' )
pp    ( '--------- local utilities imports done  -------------- ' )

#
# any constants or global (module-wide) definitions go here...
#

pp    ( ' ' ) 
pp    ( '--------- constants and globals defined ... ---------- ' )


# ---- chop off semicolon ---- 

def chop_off_semicolon ( qrystring ):

  retval = str.rstrip ( qrystring )
  n_last = len(retval) - 1

  if retval [ n_last ] == ';':
    retval = retval[:-1] 
    # print( 'sql stmnt chopped: [', retval, ']' )

  return retval # ---- chopped off semincolon ---- 


# --- the output handle: need this to convert vector to list ------ 

def output_type_handler(cursor, metadata):
    if metadata.type_code is oracledb.DB_TYPE_VECTOR:
        return cursor.var(metadata.type_code, arraysize=cursor.arraysize,
                          outconverter=list)

# ------ start of main ---------- 

pp    ( ' ' ) 
pp    ( '--------- functions defined, start of MAIN..  ---------- ' )
pp    ( ' ' ) 

ora_conn = ora_logon () 
  
pp    ( '-----------------  connection opened ------------- ' )

# ora_sess_inf2 ( ora_conn ) 
# pp    ( ' ' )
# pp    ( "-----------------  1st session info.. ------------- " )
# pp    ( ' ' )
# pp    ( ' At this point, should have 3+1 RoundTrips and 1-2 centiseconds of DB time. ' )
# pp    ( ' ' )

# prepare to handle vectors -> lists 
# sigh, do I really have to specify this... ?
ora_conn.outputtypehandler = output_type_handler

# --- check arguments ----- 

# now start sql and real work

# if arg1: use it as SQL..
if len(sys.argv) == 2:
  sql_for_qry = sys.argv[1] 
else:
  print    ( ' ' )
  sql_for_qry = input ( "do_sql.py: SQL > " )

sql_for_qry = chop_off_semicolon ( sql_for_qry ) 

# pp ( ' creating cursor... ' ) 
cursor = ora_conn.cursor()     

pp    ( ' ' )
pp    ( 'Rownr micro_sec     Content' )
pp    ( '----- ------------  ----------... ' )

start_ns = time.perf_counter_ns()
for row in cursor.execute ( sql_for_qry ): 
  next_ns         = time.perf_counter_ns()      # can this be made µsec faster in 1 line ? 
  # diff_micro_sec  =  ( next_ns - start_ns ) / 1000        # we dont need round..
  diff_micro_sec  = round ( ( next_ns - start_ns ) / 1000 ) # we dont need round..
  start_ns        = next_ns
  pp   ( f"{cursor.rowcount:5d}", f"{diff_micro_sec:12,.0f}"
       , row )

pp    ( ' ' ) 
pp    ( '.. Query was : -[', sql_for_qry, ']-' )
pp    ( ' ' ) 

# ora_sess_inf2 ( ora_conn )

# pp    ( ' ' )
# pp    ( ' proc_time [ns]: ',  f"{time.process_time_ns():13,.0f}" )
# pp    ( ' tmr_total  [s]: ',  f"{tmr_total():3.6f}", '\t\t, total since set-start.' )
# pp    ( ' ' )

tmr_spin ( 2 )      # give it 2 sec, to show some time worked..

ora_sess_info ( ora_conn ) 

ora_time_spent ( ora_conn ) 

pp    ( ' ' ) 
pp    ( '---- end of do_sql_times.py ---- ' )
pp    ( ' ' ) 

