import subprocess

# Open the argument file and get kit
with open('/home/bella/fluent/Variables/QuantITargs.txt', 'r') as quantArgs:
    line = quantArgs.readline()
    args = line.replace('\"','').strip().split(',')
    kit = args[0]

# Copy stdCurve before latest to active stdCurve
stdBackup = '/home/bella/fluent/Variables/%sStdCurve-BackUp.txt' % kit
stdTXT = '/home/bella/fluent/Variables/%sStdCurve.txt' % kit

# Open stored standard curve backup
stdCurves = []
with open(stdBackup, 'r') as sB:
    lines = sB.read().split('\n')
    x = 0

    # Each standard curve spans 3 lines, store together
    while lines[x]:
        stdCurves.append( lines[x:x+3] )
        x += 3

# Open the file with the active standard curve and replace with the curve before the latest
with open(stdTXT, 'w') as sT:
    sT.write( '\n'.join(stdCurves[-2]) )

# Open the argument file and set to not create a new standard curve
with open('/home/bella/fluent/Variables/QuantITargs.txt', 'w') as quantArgs:
    quantArgs.write('\"%s\",\"No\"' % kit)

# Copy stdCurve PNG before latest to active stdCurve
pngPath = '/home/bella/fluent/Variables/StdCurves/%sStdCurve-%s.png' % (kit, stdCurves[-2][0])

cpCommand = "cp %s /home/bella/fluent/Variables/%sStdCurve.png" % (pngPath, kit)
subprocess.run(["bash","-c", cpCommand])

