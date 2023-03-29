# Pseudocode Interpreter

Interpreter for pseudocode syntax

# Pseudo ASM

Virtual Machine to run pseudo-ASM syntax

## Usage

```
usage: asmvm [flags] <sourcefile.s>
flags:
	--instruction	show each instruction after each clock_cycles
	-d, --debug  	enable real time debugging
	-s, --step   	wait for a predefined time after each cycle
	-t, --table  	draw a complete trace table for the program - not compatible with other representations
	--acc        	show accumulator status after each cycle
	--ix         	show index register status after each cycle
	--pc         	show program counter status after each cycle
 ```

## Syntax

### Number notation
 - `#n` denary
 - `&n` hexadecimal
 - `Bn` binary
 
### Registers

 - `ACC` Accumulator
 - `IX` Index Register
 - `PC` Program counter

### Flags
 - `flagname: opcode arg1` code flag
 - `flagname:` | `flagname: #n` data flag : stored into main memory

### Instruction Set
 - `LDM #n` load n into ACC
 - `LDR #n` load n to IX
 - `LDD <address>` load contents of address into ACC
 - `LDI <address>` address to load from is stored at address
 - `LDX <address>` address to load from is formed by address + contents of IX : copy contents to ACC
 - `MOV <register>` move contents of ACC to the given register
 - `STO <address>` store contents of ACC at the given address
 - `ADD #n | <address>` add n or contents of address to ACC
 - `SUB #n | <address>` sub n or contents of address to ACC
 - `INC <register>` increment by 1 the contents of register
 - `DEC <register>` decrement by 1 the contents of the register
 - `AND #n | <address>` bitwise AND of n or address with ACC : store result at ACC
 - `XOR #n | <address>` bitwise XOR of n or address with ACC : store result at ACC
 - `LSL #n` shift left n positions contents of ACC : add 0's
 - `LSR #n` shift right n positions contents of ACC : add 0's
 - `OR #n | <address>` bitwise OR of n or address with ACC : store result at ACC
 - `CMP #n | <address>` compare n or contents of address to ACC : result is stored in ZF inside EFLAGS
 - `CMI <address>` compare contents of address stored at address to ACC
 - `JMP <address>` unconditional jump to address
 - `JPE <address>` conditional jump : jump if equal
 - `JPN <addresS>` conditional jump : jump if not equal
 - `IN` give controll to command line and input 1 character (byte) into ACC as ASCII
 - `OUT` output to screen the contents of ACC encoded as ASCII
 - `END` return control to the operating system
 
### Example

```asm
// Key in 1 character and display the next max (5) characters after in ASCII order
in
sto char
// Output newline character x0A
ldm &0A
out
loop: ldd char
inc acc
sto char
out
ldd count
inc acc
sto count
cmp max
jpn loop
end

char: #0
count: #0
max: #5
```

Example usage for ASM debugging using the tracetable mode

![error displaying image -> image.png](image.png?raw=true "Title")
