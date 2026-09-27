#
# tsthist.py : generate sql_history for testing..
#
# purpose: 
#   execute some sql, and report on history
#   
# todo:
# - allow cli arguments.. 
# - on create-table, return exist yes/no/error
# - on history: if >10 lines, report version, enabled, total, and buffer-size.
# - if no history possible: is it parameter, or version, or other ?
# 
# 

print ( ' ' )
print ( '--------- start testing... ---------- ' )
print ( ' ' )

import    os
import    sys
import    array

import    random
import    string

import    time
from      datetime      import datetime
from      dotenv        import load_dotenv

import    oracledb

print ( '--------- generic imports done, import local utils  -------------- ' )
print ( ' ' )

from    prefix        import *
from    ora_login     import *
# from    duration      import *
# from    inspect_obj   import *

# in case we use tmr from duration.py ...
# tmr_start ()

pp    ( ' ' )
pp    ( '--------- local utilities imports done, define globals  -------------- ' )

# name to set module, if we want to use that..
g_ora_module = 'sql_hist_test'

def hit_any_key ( s_prompt ):
  some_input = input ( f_prfx() + s_prompt +  ' ...enter... > ' )
  return some_input

def f_hist_cre_content_table ( ora_conn ): 

  sql_cre_tab="""
    BEGIN /* hist_01 cre-tab */
      execute immediate 'create table xx_content (
           id          number   generated always as identity not null primary key
        ,  created_dt timestamp default systimestamp
        ,  payload    varchar2(1000)
        ) ';
      execute immediate ' create index xx_content_dt on xx_content ( created_dt, id ) ' ;
    EXCEPTION
      when OTHERS then
        if SQLCODE = -955 then -- name used..
          null;
          dbms_output.put_line ( 'table exists.... ' ) ;
        else
          RAISE; -- re-raise unexpected errors
        end if;
    END;
  """
  # no bind vars.. can just execute

  cur_cre_tab = ora_conn.cursor()
  cur_cre_tab.execute ( sql_cre_tab )

  return 0 

def f_hist_gen_content ( ora_conn, nr_recs, txt_like ):

  sql_hist_payload = """
    insert /* hist_02 get payload */ into xx_content ( payload)
    select substr ( text, 1, 900 )
    from dba_source
    where text like :b_txt_like 
    and rownum <= :b_nr_recs
  """
  # 2 input bindvars: b_txt_like, b_nr_recs
  
  cur_hist_ins = ora_conn.cursor ()

  # why do we need local copies ?? 
  l_nr_recs = nr_recs
  l_like = txt_like

  cur_hist_ins.execute ( sql_hist_payload, b_txt_like = l_like, b_nr_recs = l_nr_recs )
  
  n_retval = cur_hist_ins.rowcount 

  return n_retval

# single insert
def f_ins_content ( ora_conn, payload ):

  sql_ins_single = """
    insert into xx_content ( payload ) values ( :b_payload )
  """
  # 1 bind var: payload
  
  l_payload = payload   # why need copy to local.. ? 
  cur_ins   = ora_conn.cursor ()
  cur_ins.execute ( sql_ins_single, b_payload = l_payload )

  return 1

pp    ( ' ' )
pp    ( '--------- local constants and functions defined, start of main..  ---------- ' )
pp    ( ' ' ) 
       
ora_conn        = ora_logon ()

# set module, good habit..
module_id       = ora_get_mod ( ora_conn, g_ora_module )
ora_conn.module = module_id

pp    ( ' ' )
pp    ( '-----------------  connection opened ------------- ' )
pp    ( ' ' )

ora_sess_info ( ora_conn )

pp    ()
pp    ( 'initial session stats ... ' ) 
pp    ( )
# hit_any_key ( 'initial sess_info...  ' ) 

f_hist_cre_content_table ( ora_conn) 

total_rows   = 0 
max_recs     = 2000000
txt_like     = '%yz%'

nr_rows      =  f_hist_gen_content ( ora_conn, max_recs, txt_like )
total_rows += nr_rows

pp    ('generated', nr_rows, 'from clause [', txt_like, ']' )
pp    ( )
pp    (         'nr rows: ' + str ( nr_rows) + '...'  ) 
# hit_any_key ( 'nr rows: ' + str ( nr_rows) + '...'  ) 

# do a nr of loops

for n_loop in range (1, 5 ):
  txt_like  = '%' + str ( n_loop ) + 'x%' 
  nr_rows  +=  f_hist_gen_content ( ora_conn, max_recs, txt_like )
  pp        ( 'gen_content:', nr_rows, 'like: [', txt_like, ']' )
  total_rows += nr_rows
  pass

pp    ('generated some rows in loops.' )
pp    ( )
pp    (         'nr rows generated is now: ' + str ( total_rows ) + '...'  ) 
# hit_any_key ( 'nr rows generated is now: ' + str ( total_rows ) + '...'  ) 

# now do some high-freq stmnts

all_chars = string.ascii_letters + string.digits
add_nr_rows = 1000

pp    ('Generating ', add_nr_rows, ', one by one...' ) 

for n_loop in range (1, add_nr_rows + 1):
  payload = 'singlerow: ' + str ( n_loop) + ''.join(random.choices(all_chars, k=900))
  f_ins_content ( ora_conn, payload ) 
  total_rows += 1

ora_conn.commit()  # doing row-commit doubles the roundtrips..

pp    ('generated single rows,'  )
pp    ( )
pp            ( 'nr rows generated is now: ' + str ( total_rows ) + '...'  ) 
# hit_any_key ( 'nr rows generated is now: ' + str ( total_rows ) + '...'  ) 

pp ()
pp ()
ora_sess_hist ( ora_conn ) 

pp    ()
pp    ( 'session History (v23 only), check SQLs done... ' ) 
pp    ()
# pp  (         'Check v$sql_history... '  ) 
# hit_any_key ( 'Check v$sql_history... '  ) 

# pp ()
# pp ()
# ora_module_sqlarea ( ora_conn, g_ora_module ) 

# pp    ()
# pp    ( 'SQL done by module (all versions), check SQLs listed... ' ) 
# pp    ()
# some_input = input ( ".. .. .. .. .. ...enter... > " )

# pp ()
# pp ()
# ora_module_sqlarea ( ora_conn, module_id ) 

# pp    ()
# pp    ( 'SQL done by SESSION (all versions), check SQLs listed... ' ) 
# pp    ()
# some_input = input ( ".. .. .. .. .. ...enter... > " )

pp ()
# ora_sess_info ( ora_conn ) 

pp ()
ora_time_spent ( ora_conn )

pp    ( ' ' )
pp    ( '---- end of ... ---- \n' )
