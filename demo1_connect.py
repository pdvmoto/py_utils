#
# demo1_connect.py : show how to connect
#

print ( ' ' ) 
print ( '--------- demo1_connect.py: show how to connect ... ---------- ' )

import    os
import    sys

import    time
from      datetime      import datetime
from      dotenv        import load_dotenv

import    oracledb 

print ( ' ' )
print ( "--------- generic imports done  -------------- \n" )

from      duration      import *
from      prefix        import *
from      ora_login     import *


pp    ( ' ' )
pp    ( "--------- local utilities imports done  -------------- " )

#
# any constants or global (module-wide) definitions go here...
#

pp    ( ' ' ) 
pp    ( '--------- constants and globals defined ... ---------- ' )

pp    ( ' ' ) 
pp    ( '--------- functions defined, start of main..  ---------- ' )

ora_conn = ora_logon () 
  
pp    ( "------------ Connection opened, End of Demo1 ------------- " )

# optional: show session-info, 
# optional: ping-db 
# optional: show RDBMS-info

quit ()
