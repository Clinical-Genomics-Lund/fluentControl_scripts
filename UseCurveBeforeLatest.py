import subprocess
from datetime import datetime

# Open the argument file and get kit
with open("C:\\Tecan\\Variables\\QuantITargs.txt", 'r') as quantArgs:
  line = quantArgs.readline()
  args = line.replace('\"','').strip().split(',')
  kit = args[0]

# Copy stdCurve before latest to active stdCurve
stdBackup = 'C:\\Tecan\\Variables\\%sStdCurve-BackUp.txt' % kit
stdTXT = 'C:\\Tecan\\Variables\\%sStdCurve.txt' % kit

# Open stored standard curve backup
stdCurves = []
with open(stdBackup, 'r') as sB:
  lines = sB.read().split('\n')
  x = 0

  # Each standard curve spans 3 lines, store together
  while lines[x]:
    stdCurves.append( lines[x:x+3] )
    x += 3

with open(stdTXT, 'r') as sT:
  line = sT.readline()
  currentStdCurveDate = datetime.strptime(line.strip(), "%Y%m%d-%H%M%S")

# Open the file with the active standard curve and replace with the curve before the latest
with open(stdTXT, 'w') as sT:
  for i in range((len(stdCurves) - 1),0,-1):
    stdCurveDate = datetime.strptime(stdCurves[i][0], "%Y%m%d-%H%M%S")

    if stdCurveDate < currentStdCurveDate:
      sT.write( '\n'.join(stdCurves[i]) )
      stdCurveDate = stdCurves[i][0]
      break

# Open the argument file and set to not create a new standard curve
with open('C:\\Tecan\\Variables\\QuantITargs.txt', 'w') as quantArgs:
  quantArgs.write('\"%s\",\"Yes\"' % kit)

# Copy stdCurve PNG before latest to active stdCurve
pngPath = 'C:\\Tecan\\Variables\\StdCurves\\%sStdCurve-%s.png' % (kit, stdCurveDate)

cpCommand = "copy /Y %s C:\\Tecan\\Variables\\%sStdCurve.png" % (pngPath, kit)
print(cpCommand)
subprocess.call(cpCommand, shell=True)
