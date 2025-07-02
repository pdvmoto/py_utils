# inspect a python object:
# show type, dir, length, rep, and more..
# ------------------------------------------------

# this prefix seems to remain local to functions in the file?

def f_prfx():
  return "inspect_obj (selftest) : "

def f_inspect_obj( s_objname, o_obj ):

  print ( f_prfx(), "-------- Object :", s_objname, "--------" )

  print ( f_prfx(), "o_obj -[", o_obj, "]-" )
  print ( f_prfx(), "o_obj type  : ",  type (o_obj ) )

  if o_obj != None:
    if hasattr ( o_obj, 'len' ):
      obj_len = len ( o_obj ) 
    else:
      obj_len = 0

    print ( f_prfx(), "o_obj length: ",  obj_len )
    print ( f_prfx(), "o_obj dir   : ",  dir (o_obj ) )
    print ( " " )
    # hit_enter = input ( f_prfx() + "meta data from " + s_objname + "...., hit enter.." )

    print ( "--- repr --->" )
    print ( f_prfx(), "o_obj repr  : ",  repr ( o_obj ) )
    print ( "<--- repr ---  " )

  # only if obj is not empty

  print ( f_prfx(), " ------ inspected o_obj ", s_objname, " ---------- " )
  hit_enter = input ( f_prfx() + "about to go back...., hit enter.." )

# end of f_inspect_obj, show properties of an object

# self-test..

if __name__ == '__main__':


  print ()
  print ( f_prfx(), ' ----- Self Test of inpect_obj ------ ' ) 
  print ()

  lst  = [1, 2,3 ]
  f_inspect_obj ( 'lst', lst )

  print ()
  print ( f_prfx(), ' ----- Self Test done ------ ' )
  print ()
