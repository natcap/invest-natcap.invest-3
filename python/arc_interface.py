#The Arc interface to the invest core.
#This interface will take the UI code

import invest_core.lhl

def arcInterface():
  print "Made it to the Arc interface!"
  invest_core.lhl.invokeHelper() 
  print "finished in Arc interface!"
  return

