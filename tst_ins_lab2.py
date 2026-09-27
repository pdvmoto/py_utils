#
# tst_ins_lab2.py : demo sql_history using existing tst_ins_label
#
# background:
#   re-use insert-program
#   add ora_sess_hist () 
#
# notice:
# - no COMMIT in (helper, TAPI) functions.
# - ... enable sql_history, only against oracle 23ai.
#
# idea: 
# - create an empty list itl_list = [] 
# - on insert: only add element to list itl_list.append ( (...) )  
# - if  (len(itl_list) > max_lenght ) : 
#     itl_list_2db()          # dump list into table, do not commit..
#     itl_list = []           # re-initialize empty list
# - and dont forget: a final call to empty-out the list before commit...
#
# todo: specific for timer-version
#   - test if array is empty: done
#   - turn into importable module for re-use
#   - add perf_counter and process_time.
#   - ...
#
# todo 
# - also test ins-vector
# - use try-except to handle and report errors
# - test with epoch-timestamp, exact timing when + what..
# - Graceful Exit on SQL-error (gently report ORA-00942 etc..).
# - report program-stats (time..) and sql-stats (make it optional...)
#

print ( ' ' ) 
print ( '--------- start testing... ---------- ' )
print ( ' ' ) 

import    os
import    sys
import    array

import    time
from      datetime      import datetime
from      dotenv        import load_dotenv

import    oracledb 

print ( '--------- generic imports done, import local utils  -------------- ' )
print ( ' ' )

from    prefix        import *
from    ora_login     import *
from    duration      import *
# from    inspect_obj   import *

pp    ( ' ' )
pp    ( '--------- local utilities imports done, define globals  -------------- ' )

# in case we want timer...
tmr_start () 

#
# any constants or global (module-wide) definitions go here...
#

# -- -- -- -- Constants and global list for Array inserts  -- -- -- -- -- 

g_module_name = 'module_ins_label'

itl_list         = []           # empty list for records, to be filled, inserted, re-used
itl_list_max_len = 1000         # trigger SQL-Insert, and use for prefecth/arraysizes

itl_list_sql_ins = """
INSERT /* t2 list  */ into tst_item_label
       (   itm_id,   src_id,   label,   label_score,   label_comment )
VALUES ( :bitm_id, :bsrc_id, :blabel, :blabel_score, :blabel_comment )
"""

itl_ins_t34 = """
INSERT /* t3/4 indv */ 
  into tst_item_label ( itm_id, src_id,  label_score, label_comment, label )
  select                itm_id, src_id , label_score, 'add run 3/4'  
       , replace ( replace ( label, 't1', 't3' ), 't2', 't4' ) 
  from  tst_item_label
  where 1=1 
  and id = :b_id
""" 
# needs just 1 input-bind


pp    ( ' ' ) 
pp    ( '--------- constants and globals defined, now functions ... ---------- ' )


# --- the oracle output handle: need this to convert vector to list ------ 

def output_type_handler(cursor, metadata):
    if metadata.type_code is oracledb.DB_TYPE_VECTOR:
        return cursor.var(metadata.type_code, arraysize=cursor.arraysize,
                          outconverter=list)

# --- the original function... ------------

# cursor with variable for returning.
# note: try prepare / parse ?  didnt help much...?

def f_ins_label ( itm_id, src_id, label, label_score, label_comment ):

  sql_ins_label = """
  INSERT /* t1 indiv */ into tst_item_label
         (   itm_id,   src_id,   label,   label_score,   label_comment )
  VALUES ( :bitm_id, :bsrc_id, :blabel, :blabel_score, :blabel_comment )
  RETURNING id into :bnw_id
  """

  ins_itl_cur = ora_conn.cursor()
  nw_id       = ins_itl_cur.var(int)

  # do the insert, input-bind-var => local_var
  ins_itl_cur.execute ( sql_ins_label
                       , bitm_id        = itm_id
                       , bsrc_id        = src_id 
                       , blabel         = label
                       , blabel_score   = label_score
                       , blabel_comment = label_comment
                       , bnw_id         = nw_id )

  # catch out-var, the nw_id
  retval = nw_id.getvalue()[0]
  return retval

# ----------- end f_ins_labels, return ID of new label -----

def f_ins_lab2 ( id ):
  
  # sql is defined as global-constant, 1 bind v1ar, bid

  ins_itl_lab2 = ora_conn.cursor()
  # nw_id       = ins_itl_lab2.var(int)

  # do the insert, input-bind-var => local_var
  ins_itl_lab2.execute ( itl_ins_t34
                       , b_id = id 
                      )

  # catch out-var, the nw_id
  # retval = nw_id.getvalue()[0]

  return 0

# ----------- end f_ins_lab2, return ID of new label -----

# function to insert the list-values (when max-len, or at end of program.... )

def f_ins_label_list2db ( ):

  global itl_list       # allow this function to modify the global list

  if ( len ( itl_list )  < 1 ):
    pass
    # pp ( ' list2db, empty list, no action ' ) 
    return 0 

  itl_cur = ora_conn.cursor ()

  # use the (global-)constant for SQL, and the global itl_list for data
  itl_cur.executemany ( itl_list_sql_ins, itl_list )

  # pp ( ' list2db: inserted, list length:', len ( itl_list ), ' rowcount:', itl_cur.rowcount ) 

  # re-initialize the list..
  itl_list = [] 

  return itl_cur.rowcount   # report the nr of records inserted

# function to fill the list (and check max-len)

def f_ins_label_add2list ( itm_id, src_id, label, label_score, label_comment ):

  global itl_list       # allow this function to modify the global list

  itl_list.append ( ( itm_id
                    , src_id
                    , label
                    , label_score
                    , label_comment ) )

  if ( len ( itl_list ) > itl_list_max_len ):  # time to transfer the list?

    n_2db = f_ins_label_list2db ()

  else:

    n_2db = 0   # no records got inserted to RDBMS on this pass

  # inserted, if lenght..

  return n_2db  #  nr of records added to db.


# ---- chop off semicolon ----

def chop_off_semicolon ( qrystring ):

  retval = str.rstrip ( qrystring )
  n_last = len(retval) - 1

  if retval [ n_last ] == ';':
    retval = retval[:-1] 
    # print( 'sql stmnt chopped: [', retval, ']' )

  return retval # ---- chopped off semincolon ---- 


# -- execute a select and report to stdout.. 

def f_do_sql_select ( the_conn, the_sql ):

  # future options: report micorsec, report timeing, report summary..

  sql_for_qry = chop_off_semicolon ( the_sql )

  # if nothing entered: return now
  
  pp    ( ' ' )
  pp    ( 'Rownr (Content)' )
  pp    ( '----- ----------... ' )

  cursor = the_conn.cursor()
  for row in cursor.execute ( sql_for_qry ):
    pp   ( f"{cursor.rowcount:5d}", row )

  pp    ( ' ' )
  pp    ( '.. Query was : -[', sql_for_qry, ']-' )
  pp    ( '..', cursor.rowcount, ' rows processed.' )
  pp    ( ' ' )

  n_retval = cursor.rowcount

  return n_retval

# -- function to do manual-input-sql, wait for keyboard..
# -- note: must be select ..

def f_do_manual_sql ( the_conn ):

  pp    ( ' ' )
  sql_for_qry = input ( "do_sql.py: SQL > " )

  # if nothing entered: return now
  if not sql_for_qry:
    return 0
  
  sql_for_qry = chop_off_semicolon ( sql_for_qry )

  pp    ( ' ' )
  pp    ( '.. processing...' )
  pp    ( ' ' )
  pp    ( 'Rownr (Content)' )
  pp    ( '----- ----------... ' )

  cursor = the_conn.cursor()
  for row in cursor.execute ( sql_for_qry ):
    pp   ( f"{cursor.rowcount:5d}", row )

  pp    ( ' ' )
  pp    ( '..', cursor.rowcount, ' rows processed.' )
  pp    ( ' ' )
  pp    ( '.. Query was : -[', sql_for_qry, ']-' )

  pp    ( ' ' )

  n_retval = cursor.rowcount
  return n_retval

# ---- do some inserts.. ---- 
def do_indiv_inserts ( ora_conn, nr_ins ):

  pp ( ' ' ) 
  pp ( 'Start: run test indiv for ', nr_ins, ' inserts.' )

  # now loop for n_sec..
  n_counter = int ( 0 )
  start_t = datetime.now().timestamp()        # time.time()

  itm_id = 1
  src_id = 1

  n_counter = int ( 0 )
  while n_counter < nr_ins:

    label         = 'indiv t1' + '_' + str ( n_counter )
    label_comment = 'individual label=' + str(n_counter)
    label_score   = 1 - ( 1 / (n_counter+1) )  

    f_ins_label ( itm_id, src_id, label, label_score, label_comment )

    n_counter = n_counter + 1

  # end while loop
    
  pp    ( ' ' )
    
  end_t   = datetime.now().timestamp()

  return n_counter

# ------ end of f_do_indiv_insert ------


# create a test-table if possible
f_cre_tst_tbl ( the_conn ):

  sq_cre_tst_tbl="""o
  creat if not exists 
  """

  return n_retval

# ------ created test table ------ 


# ------ start of main ---------- 

pp    ( ' ' ) 
pp    ( '--------- functions defined, start of main..  ---------- ' )
pp    ( ' ' ) 

# pp    ( ' proc_time_ns and time : ',  f"{time.process_time_ns():12,.0f}", ' time: ', time.time() )
# pp    ( ' ' )

ora_conn = ora_logon () 

module_name     = ora_get_mod ( ora_conn, g_module_name ) 
ora_conn.module = module_name

# output-handler, only needed for vectors
# ora_conn.outputtypehandler = output_type_handler

pp    ( ' ' )
pp    ( '-----------------  connection opened ------------- ' )
pp    ( ' ' )

ora_sess_info ( ora_conn ) 

ora_sess_hist ( ora_conn ) 

pp    ( '1st history shown, Enter to continue... ' )
some_input = input ( ".. .. .. .. ...enter... > " )

# pp    ( ' ' )
# pp    ( ' At this point, should have a few RoundTrips and 1-2 centiseconds of DB time. ' )
# pp    ( ' ' )

# --- check arguments ----- 

# n = len(sys.argv)

# Arguments passed
# pp ("Name of Python script:", sys.argv[0])
# pp ("Total arguments passed:", n)
# pp ("Arguments passed:")
# for i in range(1, n):
#   pp ('..arg ' , i, ': [', sys.argv[i], ']')

# now start sql and real work

itm_id = 1
src_id = 1
label = 'first label'
label_comment = 'comment  itm_id=' + str(itm_id) + ', src_id=' + str(src_id)
label_score = 1 - ( 1 / itm_id )  

# 1 insert, originally this was the test of the function
pp    ( 'Inserting Label ', label ) 
pp    ( ' ' )
f_ins_label ( itm_id, src_id, label, label_score, label_comment )

pp    ( 'one label inserted, check history ' )

ora_sess_info ( ora_conn ) 
ora_sess_hist ( ora_conn ) 

pp    ( ' ' )
pp    ( 'one insert done, how history, Enter to continue... ' )
some_input = input ( ".. .. .. .. .. ...enter... > " )

# now do a series of inserts..
nr_ins = 200
do_indiv_inserts ( ora_conn, nr_ins )

pp    ( 'added ', nr_ins, 'inserts via t1 , check history ' )

ora_sess_info ( ora_conn ) 
ora_sess_hist ( ora_conn ) 

pp    ( 'added ', nr_ins, 'inserts via t1 , check history ' )
some_input = input ( "...enter... > " )

# now do a series of inserts..
nr_ins = 20
do_indiv_inserts ( ora_conn, nr_ins )

pp    ( 'added ', nr_ins, 'inserts via t1 , check history ' )

ora_sess_info ( ora_conn ) 
ora_sess_hist ( ora_conn ) 

pp    ( 'added ', nr_ins, 'inserts via t1 , check history ' )
some_input = input ( "...enter... > " )

# now do a timed series of inserts..
n_sec_test = 1.1

pp ( ' ' ) 
pp ( 'Start: run test indiv for ', n_sec_test, ' sec.' )

# now loop for n_sec..
n_counter = int ( 0 )
start_t = datetime.now().timestamp()        # time.time()
end_t   = start_t + n_sec_test

itm_id = 1
src_id = 1

n_counter = int ( 0 )
while datetime.now().timestamp() < end_t:   # time.time() < end_t:

  label         = 'label t1' + '_' + str ( n_counter )
  label_comment = 'comment  label=' + str(n_counter)
  label_score   = 1 - ( 1 / itm_id )  

  f_ins_label ( itm_id, src_id, label, label_score, label_comment )

  n_counter = n_counter + 1

# end while loop
  
pp    ( ' ' )
pp    ( 'done, nr loops:', n_counter, ', f_ins speed:', round ( n_counter / n_sec_test, 2) , ' records/sec.' )
pp    ( ' ' )

ora_conn.commit()

## ora_sess_info ( ora_conn ) 

ora_sess_hist ( ora_conn ) 

pp    ( 'added ', n_counter, 'inserts via t1, in', n_sec_test, 'seconds , check history ' )
some_input = input ( "...enter... > " )


pp    ( ' Committed -- -- -- -- -- end of first indiv test, next try list -- -- -- -- ' ) 
pp    ( ' ' )

## ora_sess_info ( ora_conn ) 

n_sec_test = 1.5

pp ( ' ' ) 
pp   ( 'Start: run test list for ', n_sec_test, ' sec.' )
pp ( ' ' ) 

# now loop for n_sec.., use list to buffer
n_counter = int ( 0 )
n_2db     = 0 
start_t   = datetime.now().timestamp()        # time.time()
end_t     = start_t + n_sec_test

itm_id = 1
src_id = 1

while datetime.now().timestamp() < end_t:   # time.time() < end_t:

  label         = 'label t2 add2list' + '_' + str ( n_counter ) 
  label_comment = 'comment  label2list=' + str(n_counter)
  label_score   = 1 - ( 1 / itm_id )  

  n_2db = n_2db + f_ins_label_add2list ( itm_id, src_id, label, label_score, label_comment )

  n_counter = n_counter + 1

# end while loop
  
# Important: empty out the list, keep total
n_2db = n_2db + f_ins_label_list2db () 

# pp ( '.. and test deliberately empty list ' ) 
# test deliberately empty list..
# itl_list = []
# n_2db = n_2db + f_ins_label_list2db () 

pp    ( ' ' )
pp    ( 'done, nr loops:', n_counter, ', list2db speed:', round ( n_counter / n_sec_test, 2) , ' records/sec.' )
pp    ( ' ' )

#ora_sess_info ( ora_conn ) 

ora_conn.commit()

pp    ( ' ' )
pp    ( ' Committed -- -- -- -- -- end of list test, list inserted -- -- -- -- ' ) 

# duplicate id 1000
# itl_ins_t34
f_ins_lab2 (  1000 )
f_ins_lab2 ( 10000 )

# now loop for n_sec.., use lab2: duplicate records
n_counter = int ( 0 )
n_2db     = 0 
start_t   = datetime.now().timestamp()        # time.time()
end_t     = start_t + n_sec_test

itm_id = 1
src_id = 1

while datetime.now().timestamp() < end_t:   # time.time() < end_t:

  n_2db = n_2db + 1
  f_ins_lab2 ( n_counter )

  n_counter = n_counter + 1

# end while loop

pp    ( ' ' )
pp    ( 'done, nr loops:', n_counter, ', lab2 speed:', round ( n_counter / n_sec_test, 2) , ' records/sec.' )
pp    ( ' ' )

pp    ( 'loops done, show history... ' )
ora_sess_hist ( ora_conn ) 

the_sql="select /* t6 */ spinf_n( 1 ) from dual connect by level < 3" 

f_do_sql_select ( ora_conn, the_sql )

pp            ( 'spin done, show hist...' ) 
ora_sess_hist ( ora_conn ) 

# show contents of v$sql
  
sql_vsql = """
  select s.sql_id
  , s.executions                            as nr_exe
  , s.elapsed_time                          as ela_us
  , s.cpu_time                              as cpu_us
  --, s.elapsed_time / s.executions           as us_p_exe
  , substr ( s.sql_text, 1, 60 )            as sql_txt 
  from v$sqlarea  s
  where s.sql_text like '%/* t%'               -- only watermarked stmnts
  order by s.elapsed_time
"""

pp            ( 'check v$sql, then show hist...' ) 

f_do_sql_select ( ora_conn, sql_vsql )

ora_sess_hist ( ora_conn ) 

pp    ( 'check v$sql, history shown, Enter to continue... ' )
some_input = input ( "...enter... > " )


# call a function to do another SQL, manual-input ? 
f_do_manual_sql ( ora_conn )

pp            ( 'manual SQL done, show history...' )
ora_sess_hist ( ora_conn ) 

ora_module_sqlarea ( ora_conn ) 

pp ( )
ora_sess_info ( ora_conn ) 

pp ( )
pp ( 'list SQL for this run only, (SID,SEERIAL#) ' )
module_name = ora_get_mod ( ora_conn, g_module_name ) 
ora_module_sqlarea (          ora_conn,   module_name ) 

pp ( )
pp ( 'list SQL for All runs of ', g_module_name + '%' )
ora_module_sqlarea (      ora_conn, g_module_name ) 

pp ()
pp ( 'SQL for ALL of INSTANCE... ' ) 
ora_sqlarea ( ora_conn ) 

# pp ( )
# ora_sess_info ( ora_conn ) 

pp ( )
ora_time_spent ( ora_conn )  

# pp ( )
# tmr_report_time()

# pp    ( ' ' )
# pp    ( ' process_time [ns]: ',  f"{time.process_time_ns():13,.0f} user + sys" )
# pp    ( ' tmr_total     [s]: ',  f"{tmr_total():3.6f}", ', elapsed since (tmr_)start.' )

pp    ( ' ' )
pp    ( '---- end of ... ---- end of  ---- \n' )
