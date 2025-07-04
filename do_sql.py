#
# do_sql.py : enter a query and run it, print results
#
# background:
#   just bcse I need to learn, and I think may be useful
#   also: I needded a test-template to test utilities..
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
# todo:
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
print ( '--------- do_sql.py: enter manual queries... ---------- ' )
print ( ' ' ) 

import    os
import    sys
import    array

import    time
from      datetime      import datetime
from      dotenv        import load_dotenv

import    oracledb 

print ( ' ' )
print ( "--------- generic imports done  -------------- " )
print ( ' ' )

from      duration      import *
from      prefix        import *
from      ora_login     import *


pp    ( ' ' )
pp    ( "--------- local utilities imports done  -------------- " )
pp    ( ' ' )

#
# any constants or global (module-wide) definitions go here...
#

pp    ( ' ' ) 
pp    ( '--------- constants and globals defined ... ---------- ' )
pp    ( ' ' ) 


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
pp    ( '--------- functions defined, start of main..  ---------- ' )
pp    ( ' ' ) 

ora_conn = ora_logon () 
  
pp    ( ' ' )
pp    ( "-----------------  connection opened ------------- " )
pp    ( ' ' )

# quit ()

# prepare to handle vectors -> lists 
# sigh, do I really have to specify this... ?
ora_conn.outputtypehandler = output_type_handler


# --- check arguments ----- 

n = len(sys.argv)

# Arguments passed
# pp ("Name of Python script:", sys.argv[0])
# pp ("Total arguments passed:", n)
# pp ("Arguments passed:")
# for i in range(1, n):
#   pp ('..arg ' , i, ': [', sys.argv[i], ']')

# now start sql and real work

# if arg1: use it as SQL..
if len(sys.argv) == 2:
  sql_for_qry = sys.argv[1] 
else:
  print    ( ' ' )
  sql_for_qry = input ( "do_sql.py: SQL > " )

sql_for_qry = chop_off_semicolon ( sql_for_qry ) 

pp    ( ' ' )
pp    ( ' processing...' )
pp    ( ' ' )
pp    ( 'Rownr (Content)' )
pp    ( '----- ----------... ' )

cursor = ora_conn.cursor()
for row in cursor.execute ( sql_for_qry ):
  pp   ( f"{cursor.rowcount:5d}", row )

pp    ( ' ' )
pp    ( '..', cursor.rowcount, ' rows processed.' ) 
pp    ( ' ' ) 
pp    ( '.. Query was : -[', sql_for_qry, ']-' )
pp    ( ' ' ) 

ora_sess_info ( ora_conn )

pp    ( ' ' ) 
pp    ( '---- end of do_sql.py ---- ' )
pp    ( ' ' ) 

