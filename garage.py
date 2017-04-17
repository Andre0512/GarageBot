import time
import RPi.GPIO as GPIO
 
# Zaehlweise der Pins festlegen
GPIO.setmode(GPIO.BOARD)
 
# Pin 22 (GPIO 25) als Ausgang festlegen
GPIO.setup(26, GPIO.OUT)
 
# Ausgang 3 mal ein-/ausschalten
# Ausgang einschalten
GPIO.output(26, GPIO.HIGH)
# zwei Sekunden warten
time.sleep(2)
# Ausgang ausschalten
GPIO.output(26, GPIO.LOW)
# zwei Sekunden warten
time.sleep(2)
# Ausgaenge wieder freigeben
GPIO.cleanup()
