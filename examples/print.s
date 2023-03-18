LDM #0
STO counter
LDR #0
loop: LDX array
OUT
INC IX
LDD counter
INC ACC
STO counter
CMP #4
JPN loop
END

array: #67
#79
#68
#69

counter:
