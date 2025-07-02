
# test_utils.py:
# - inspect_object.py  : try looking inside objects
# - duration.py        : timer utilitiy
# - prefix.py          : debug and log printing utility
# - ora_logon.py

print ( ' ---- test_utils.py --- ' ) 

print ( ' ---- test_utils.py first do imports ..--- ' ) 

import    time
from      datetime  import  datetime 

print ( 'for the record: perfcount and process_time: ', time.perf_counter(), time.process_time() )
print ()

# in case we forget..
def f_prfx():
  return " localprfx: " 

# local utilities, keep/cp in same directory for now...
from  duration      import *
from  inspect_obj   import *
from  prefix        import *
from  ora_login     import *


# test code
pp    ()
pp    ( ' ----- imports done, now testing duration.py ---- ' ) 
pp    ()

print ( ' -- start  : ', tmr_start() )
print ( ' -- set    : ', tmr_set() )

time.sleep ( 1 ) 
print ( ' \n -- dur    : ', tmr_durat() )
print ( ' -- total  : ', tmr_total() )
print ( ' -- dur2   : ', tmr_durat() )
print ( ' -- re-set : ', tmr_set() )
print ( ' -- dur4   : ', tmr_durat() )

time.sleep ( 1 ) 
print ( '\n -- total4 : ', tmr_total() )
print (   ' -- dur    : ', tmr_durat() )
time.sleep ( 1) 
print ( '\n -- re-set : ', tmr_set() )
print (   ' -- dur0   : ', f" = {tmr_durat():9.5f}" )
print (   ' -- total5 : ', f" = {tmr_total():9.5f}" )

pp    ()
pp    ( ' ----- testing inspect_obj.py ---- ' ) 
pp    ()

lst  = [1, 2,3 ]  
f_inspect_obj ( 'list ', lst ) 

pp    ()
pp    ( ' ----- next testing prefix..  ---- ' ) 
pp    ()
pp    ( f_prfx(), '..with double? prefix...' )

pp    ( 'prefix = [' + f_prfx() + '] ..from pp ...' )

pp    ( 'testing pp with prefix' , 1, 2, 3 )

pp    ()
pp    ( ' ---- prefix done, next test ora_login ---- ' ) 
pp    ()


ora_conn = ora_logon ()

sql_test = """
  select object_type, count (*) 
    from user_objects
   group by object_type   
"""

cur_logon = ora_conn.cursor ()
cur_logon.execute ( sql_test )
columns = [col.name for col in cur_logon.description]
pp     ( ' cursor colums : ', columns)
for row in cur_logon:
  pp   ( ' cursor data   : ', row )
    
pp    () 
pp    ( ' ----- ora_logon: tested ---- ' )
pp    ()



pp    ()
pp    ( ' ----- next, test timers / timing. inspect_obj.py ---- ' ) 
pp    ()

pp    ( ' we want: total-time ')  
pp    ( '          process-time, ')  
pp    ( '          activ-cpu: process/total (Activ-sess) ' )
pp    ()


pp    ( 'perf_counter     : ' , time.perf_counter() ) 
pp    ( 'perf_counter_ns  : ' , time.perf_counter_ns() ) 

time.sleep ( 2) 

pp    ( 'process_time     : ' , time.perf_counter()  ) 
pp    ( 'process_time_ns  : ' , time.perf_counter_ns() ) 

pp    ( ' ----- testing done..  ---- ' ) 
