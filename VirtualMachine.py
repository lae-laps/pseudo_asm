# Virtual Machine for pseudo-ASM syntax

import os
import sys
import time

class VirtualMachine:
    def __init__(self):
        self.IX = 0                 # Index Register
        self.PC = 0                 # Program Counter
        self.ACC = 0                # Accumulator
        self.EFLAGS = 0             # Eflags register read and write with bitmasking
        self.interrupt = 0          # Interrupts buffer
        self.OUTPUT = ''            # Stores the output of the program

        self.tree = []              # Syntax tree for source
        self.source = ""            # Raw sourcecode
        self.code_flags = {}        # Code flags
        self.data_flags = {}        # Data flags

        self.MEM = []               # Memory
        self.MAX_ADDRESS = 32       # Memory size
        self.ARCH = 32              # Architecture size
        self.clock_cycles = 0       # Total clock cycles executed
        self.DELAY = 0.1            # Delay after each instruction

        self.step = False           # Wait after each cycle
        self.DEBUG = False          # Debugging state
        self.show_pc = False        # Show Program Counter after each instruction
        self.show_ix = False        # Show Index Register after each instruction
        self.show_acc = False       # Show Accumulator after each instruction
        self.show_inst = False      # Show the instruction currently being executed
        self.tracetable = False     # Show a complete tracetable

        self.valid_opcodes = ["LDM", "LDD", "LDI", "LDX", "LDR", "MOV", "STO", "ADD", "SUB", "INC", "DEC", "JMP", "IN", "OUT", "END", "AND", "OR", "XOR", "LSL", "LSR", "CMP", "CMI", "JPE", "JPN"]

    def run(self):

        self.initialize_memory()

        self.tree = []

        # Parse source into a 2D array of lines of opcodes and operands - syntax tree

        self.source = self.source.replace('\t', ' ')                                # Replace tabs with spaces to make parsing easier

        ins = self.source.split('\n')

        for i in ins:
            i = i.strip()
            if i == '' or i.startswith("//"):
                continue
            current = i.split(' ')
            current = list(filter(('').__ne__, current))                            # Delete elements which are an empty string
            self.tree.append(current)

        err = self.parse_flags()                                                    # Do a first iteration over the code and set all the flags

        if err != 0:
            self.throw_syntax_error(f"could not set flags - exit code {err}")
            return

        exceptions = 0

        for i in range(len(self.tree)):
            if len(self.tree[i]) > 2:
                exceptions += 1
                self.throw_syntax_error(f"too many arguments at instruction {i} : {' '.join(self.tree[i])}")

        if exceptions > 0:
            return

        self.debug(f"initialized syntax tree with {len(self.tree)} instructions")

        self.debug(f"starting program")

        if self.tracetable:
            self.print_head_tracetable_line()

        # Set PC to emulate index of array (virtual address) and run that line

        self.set_pc(0)                                                              # Initialize PC to 0


        while self.interrupt == 0:                                                  # Define exit interrupts
            self.next_instruction()

        # 1  -> Parsing error
        # 2  -> Runtime error
        # #  -> Virtual Machine Runtime Exception
        # 9  -> Aborted by user
        # 10 -> Program ended (naturally)

        if self.tracetable:
            self.print_tail_tracetable_line()

        self.debug(f"program exited with exit code: {self.interrupt}")

        self.debug(f"total clock cycles : {self.clock_cycles}")

    def next_instruction(self):

        buff = self.PC

        self.clock_cycles += 1

        instruction = self.tree[self.PC]

        self.set_pc(self.PC + 1)

        if self.PC >= len(self.tree):
            self.set_interrupt(1)

        if len(instruction) > 3:
            self.throw_syntax_error(f"too many arguments : {self.PC}")
            self.set_interrupt(1)
            return

        if instruction == []:                                                       # Empty instruction
            return

        # Parse the Instruction

        try:
            opcode = instruction[0].upper()

            if not self.is_valid_opcode(opcode):
                self.throw_syntax_error(f"invalid opcode : {' '.join(instruction)} : {self.PC}")
                self.set_interrupt(1)
                return

            # Switch Case the opcode

            if opcode == "LDM":
                val = self.parse_byte_representation(instruction[1])
                if val == -1:
                    self.throw_runtime_error(f"invalid value for LDM : {instruction[1]} : {self.PC}")
                    self.set_interrupt(2)
                    return
                err = self.LDM(val)
                if err != 0:
                    self.throw_runtime_error(f"exception at LDM : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "LDD":
                addr = self.parse_data_address(instruction[1])
                if addr == -1:
                    self.throw_runtime_error(f"invalid value for address : {instruction[1]} : {self.PC}")
                    self.set_interrupt(2)
                    return
                err = self.LDD(addr)
                if err != 0:
                    self.throw_runtime_error(f"invalid data or position : {addr} : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "LDI":
                addr = self.parse_data_address(instruction[1])
                if addr == -1:
                    self.throw_runtime_error(f"invalid value for address : {instruction[1]} : {self.PC}")
                    self.set_interrupt(2)
                    return

                err = self.LDI(addr)
                if err != 0:
                    self.throw_runtime_error(f"invalid address or data during LDI : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "LDX":
                addr = self.parse_data_address(instruction[1])
                if addr == -1:
                    self.throw_runtime_error(f"invalid value for address : {instruction[1]} : {self.PC}")
                    self.set_interrupt(2)
                    return

                err = self.LDX(addr)
                if err != 0:
                    self.throw_runtime_error(f"invalid address : {self.PC}")
                    self.set_interrupt(2)
                    return


            elif opcode == "LDR":
                val = self.parse_byte_representation(instruction[1])
                if val == -1:
                    self.throw_runtime_error(f"invalid value for LDR : {instruction[1]} : {self.PC}")
                    self.set_interrupt(2)
                    return
                self.LDR(val)

            elif opcode == "MOV":
                if not instruction[1].upper() == "IX":
                    self.throw_syntax_error(f"invalid register : expected \"IX\" : {self.PC}")
                    self.set_interrupt(1)
                    return

                self.MOV()

            elif opcode == "STO":
                addr = self.parse_data_address(instruction[1])
                if addr == -1:
                    self.throw_runtime_error(f"invalid address : {instruction[1]} : {self.PC}")
                    self.set_interrupt(2)
                    return

                err = self.STO(addr)
                if err != 0:
                    self.throw_runtime_error(f"invalid address : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "ADD":
                val = self.parse_byte_representation(instruction[1])
                if val == -1:
                    val = self.parse_data_address(instruction[1])
                    if val == -1:
                        self.throw_runtime_error(f"expected a valid address or direct addressing value but found none : {instruction[1]} : {self.PC}")
                        self.set_interrupt(2)
                        return
                    else:
                        err = self.ADD_INDIRECT(val)
                        if err != 0:
                            self.throw_runtime_error(f"exception at ADD instruction : {self.PC}")
                            self.set_interrupt(2)
                            return
                else:
                    err = self.ADD_DIRECT(val)
                    if err != 0:
                        self.throw_runtime_error(f"exception at ADD instruction : {self.PC}")
                        self.set_interrupt(2)
                        return

            elif opcode == "SUB":
                val = self.parse_byte_representation(instruction[1])
                if val == -1:
                    val = self.parse_data_address(instruction[1])
                    if val == -1:
                        self.throw_runtime_error(f"expected a valid address or direct addressing value : found none : {self.PC}")
                        self.set_interrupt(2)
                        return
                    else:
                        err = self.SUB_INDIRECT(val)
                        if err != 0:
                            self.throw_runtime_error(f"exception at SUB instruction : {self.PC}")
                            self.set_interrupt(2)
                            return
                else:
                    err = self.SUB_DIRECT(val)
                    if err != 0:
                        self.throw_runtime_error(f"exception at SUB instruction : {self.PC}")
                        self.set_interrupt(2)
                        return

            elif opcode == "INC":
                if not instruction[1].upper() in ["ACC", "IX"]:
                    self.throw_runtime_error(f"invalid register : {instruction[1]} : {self.PC}")
                    self.set_interrupt(2)
                    return
                err = self.INC(instruction[1])
                if err != 0:
                    self.throw_runtime_error(f"error at INC : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "DEC":
                if not instruction[1].upper() in ["ACC", "IX"]:
                    self.throw_runtime_error(f"invalid register : {instruction[1]} : {self.PC}")
                    self.set_interrupt(2)
                    return
                err = self.DEC(instruction[1])
                if err != 0:
                    self.throw_runtime_error(f"error at DEC : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "JMP":
                addr = self.parse_code_address(instruction[1])
                if addr == -1:
                    self.throw_runtime_error(f"invalid address for JMP : {self.PC}")
                    self.set_interrupt(2)
                    return
                err = self.JMP(addr)
                if err != 0:
                    self.throw_runtime_error(f"error during JMP : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "JPE":                                                                       # Jump Equal
                addr = self.parse_code_address(instruction[1])
                if addr == -1:
                    self.throw_runtime_error(f"invalid address for JPE : {self.PC}")
                    self.set_interrupt(2)
                    return
                err = self.JPE(addr)
                if err != 0:
                    self.throw_runtime_error(f"error during JPE : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "JPN":                                                                       # Jump Not Equal
                addr = self.parse_code_address(instruction[1])
                if addr == -1:
                    self.throw_runtime_error(f"invalid address for JPN : {self.PC}")
                    self.set_interrupt(2)
                    return
                err = self.JPN(addr)
                if err != 0:
                    self.throw_runtime_error(f"error during JPN : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "CMP":
                val = self.parse_byte_representation(instruction[1])
                if val == -1:
                    val = self.parse_data_address(instruction[1])
                    if val == -1:
                        self.throw_runtime_error(f"expected a valid address or direct addressing value : found none : {self.PC}")
                        self.set_interrupt(2)
                        return
                    else:
                        err = self.CMP_INDIRECT(val)
                        if err != 0:
                            self.throw_runtime_error(f"exception at CMP instruction : {self.PC}")
                            self.set_interrupt(2)
                            return
                else:
                    err = self.CMP_DIRECT(val)
                    if err != 0:
                        self.throw_runtime_error(f"exception at CMP instruction : {self.PC}")
                        self.set_interrupt(2)
                        return

            elif opcode == "CMI":
                addr = self.parse_code_address(instruction[1])
                if addr == -1:
                    self.throw_runtime_error(f"invalid address for CMI : {self.PC}")
                    self.set_interrupt(2)
                    return
                err = self.CMI(addr)
                if err != 0:
                    self.throw_runtime_error(f"error during CMI : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "END":
                err = self.END()
                if err != 0:
                    self.set_interrupt(2)
                    return

            elif opcode == "AND":
                val = self.parse_byte_representation(instruction[1])
                if val == -1:
                    val = self.parse_data_address(instruction[1])
                    if val == -1:
                        self.throw_runtime_error(f"expected a valid address or direct addressing value : found none : {self.PC}")
                        self.set_interrupt(2)
                        return
                    else:
                        err = self.AND_INDIRECT(val)
                        if err != 0:
                            self.throw_runtime_error(f"exception at AND instruction : {self.PC}")
                            self.set_interrupt(2)
                            return
                else:
                    err = self.AND_DIRECT(val)
                    if err != 0:
                        self.throw_runtime_error(f"exception at AND instruction : {self.PC}")
                        self.set_interrupt(2)
                        return

            elif opcode == "OR":
                val = self.parse_byte_representation(instruction[1])
                if val == -1:
                    val = self.parse_data_address(instruction[1])
                    if val == -1:
                        self.throw_runtime_error(f"expected a valid address or direct addressing value : found none : {self.PC}")
                        self.set_interrupt(2)
                        return
                    else:
                        err = self.OR_INDIRECT(val)
                        if err != 0:
                            self.throw_runtime_error(f"exception at OR instruction : {self.PC}")
                            self.set_interrupt(2)
                            return
                else:
                    err = self.OR_DIRECT(val)
                    if err != 0:
                        self.throw_runtime_error(f"exception at OR instruction : {self.PC}")
                        self.set_interrupt(2)
                        return

            elif opcode == "XOR":
                val = self.parse_byte_representation(instruction[1])
                if val == -1:
                    val = self.parse_data_address(instruction[1])
                    if val == -1:
                        self.throw_runtime_error(f"expected a valid address or direct addressing value : found none : {self.PC}")
                        self.set_interrupt(2)
                        return
                    else:
                        err = self.XOR_INDIRECT(val)
                        if err != 0:
                            self.throw_runtime_error(f"exception at XOR instruction : {self.PC}")
                            self.set_interrupt(2)
                            return
                else:
                    err = self.XOR_DIRECT(val)
                    if err != 0:
                        self.throw_runtime_error(f"exception at XOR instruction : {self.PC}")
                        self.set_interrupt(2)
                        return

            elif opcode == "LSL":
                val = self.parse_byte_representation(instruction[1])
                if val == -1:
                    self.throw_runtime_error(f"invalid value for LSL : {instruction[1]} : {self.PC}")
                    self.set_interrupt(2)
                    return
                err = self.LSL(val)
                if err != 0:
                    self.throw_runtime_error(f"exception at LSL : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "LSR":
                val = self.parse_byte_representation(instruction[1])
                if val == -1:
                    self.throw_runtime_error(f"invalid value for LSR : {instruction[1]} : {self.PC}")
                    self.set_interrupt(2)
                    return
                err = self.LSR(val)
                if err != 0:
                    self.throw_runtime_error(f"exception at LSR : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "OUT":                                                   # Send ACC to screen
                err = self.OUT()
                if err != 0:
                    self.throw_runtime_error(f"exception at OUT : {self.PC}")
                    self.set_interrupt(2)
                    return

            elif opcode == "IN":
                err = self.IN()
                if err != 0:
                    self.throw_runtime_error(f"exception at IN : {self.PC}")
                    self.set_interrupt(2)
                    return

            else:
                self.throw_runtime_error(f"uncaught invalid opcode : {opcode}")
                self.set_interrupt(1)
                return

        except (IndexError, ValueError):
            self.throw_runtime_error(f"missing arguments : {self.PC}")
            self.set_interrupt(2)
            return

        except Exception as err:
            self.throw_runtime_error(f"uncaught VirtualMachine exception : {err} : {self.PC}")
            self.set_interrupt(3)
            return

        # Show data for instruction according to config

        if self.tracetable:
            self.print_tracetable_frame(self.clock_cycles, instruction, buff, self.ACC, self.IX, self.OUTPUT)

        else:
            if self.show_inst:
                self.print_instruction(buff, instruction)
            if self.show_pc:
                self.print_value("PC :", buff)
            if self.show_ix:
                self.print_value("IX :", self.IX)
            if self.show_acc:
                self.print_value("ACC:", self.ACC)

        if self.step:
            time.sleep(self.DELAY)

        self.OUTPUT = ''                                                        # Delete Output

    # Opcodes

    def LDM(self, val):
        err = self.set_acc(val)
        if err != 0:
            return -1
        return 0

    def LDR(self, val):
        err = self.set_ix(val)
        if err != 0:
            return -1
        return 0

    def LDD(self, addr):
        data = self.get_mem(addr)
        if data == -1:
            return -1
        self.set_acc(data)
        return 0

    def LDI(self, addr):
        new_addr = self.get_mem(addr)
        if not self.is_valid_address(new_addr):
            return -1
        data = self.get_mem(new_addr)
        if data == -1:
            return -2
        self.set_acc(data)
        return 0

    def LDX(self, addr):
        new_addr = addr + self.IX
        if not self.is_valid_address(new_addr):
            return -1
        data = self.get_mem(new_addr)
        if data == -1:
            return -1
        self.set_acc(data)
        return 0

    def MOV(self):
        self.set_ix(self.ACC)

    def STO(self, addr):
        err = self.set_mem(addr, self.ACC)
        if err != 0:
            return -1
        return 0

    def ADD_DIRECT(self, val):
        err = self.set_acc(self.ACC + val)
        if err != 0:
            return -1
        return 0


    def ADD_INDIRECT(self, addr):
        contents = self.get_mem(addr)
        err = self.set_acc(self.ACC + contents)
        if err != 0:
            return -1
        return 0

    def SUB_DIRECT(self, val):
        err = self.set_acc(self.ACC - val)
        if err != 0:
            return -1
        return 0


    def SUB_INDIRECT(self, addr):
        contents = self.get_mem(addr)
        err = self.set_acc(self.ACC - contents)
        if err != 0:
            return -1
        return 0

    def INC(self, register):
        if register.upper() == "ACC":
            err = self.set_acc(self.ACC + 1)
            if err != 0:
                return -1
        else:
            err = self.set_ix(self.IX + 1)
            if err != 0:
                return -1
        return 0

    def DEC(self, register):
        if register.upper() == "ACC":
            err = self.set_acc(self.ACC - 1)
            if err != 0:
                return -1
        else:
            err = self.set_ix(self.IX - 1)
            if err != 0:
                return -1
        return 0

    def JMP(self, addr):
        err = self.set_pc(addr)
        if err != 0:
            return -1
        return 0

    def JPE(self, addr):
        m = self.get_eflags(0)
        if m == -1:
            return -1
        elif m == 1:
            err = self.set_pc(addr)
            if err != 0:
                return -1
        return 0

    def JPN(self, addr):
        m = self.get_eflags(0)
        if m == -1:
            return -1
        elif m != 1:
            err = self.set_pc(addr)
            if err != 0:
                return -1
        return 0

    def CMP_DIRECT(self, val):
        err = 0
        if val == self.ACC:
            err = self.set_eflags(0, 1)
        else:
            err =self.set_eflags(0, 0)
        if err != 0:
            return -1
        return 0

    def CMP_INDIRECT(self, addr):
        err = 0
        val = self.get_mem(addr)
        if val == -1:
            return -1
        if val == self.ACC:
            err = self.set_eflags(0, 1)
        else:
            err = self.set_eflags(0, 0)
        if err != 0:
            return -1
        return 0

    def CMI(self, addr):
        err = 0
        val = self.get_mem(addr)
        if val == -1:
            return -1
        if val == self.ACC:
            err = self.set_eflags(0, 1)
        else:
            err = self.set_eflags(0, 0)
        if err != 0:
            return -1
        return 0

    def END(self):
        err = self.set_interrupt(10)
        if err != 0:
            return -1
        return 0

    def AND_DIRECT(self, val):
        err = self.set_acc(self.ACC & val)
        if err != 0:
            return -1
        return 0

    def AND_INDIRECT(self, addr):
        val = self.get_mem(addr)
        if val == -1:
            return -1

        err = self.set_acc(self.ACC & val)
        if err != 0:
            return -1
        return 0

    def OR_DIRECT(self, val):
        err = self.set_acc(self.ACC | val)
        if err != 0:
            return -1
        return 0

    def OR_INDIRECT(self, addr):
        val = self.get_mem(addr)
        if val == -1:
            return -1

        err = self.set_acc(self.ACC | val)
        if err != 0:
            return -1
        return 0

    def XOR_DIRECT(self, val):
        err = self.set_acc(self.ACC ^ val)
        if err != 0:
            return -1
        return 0

    def XOR_INDIRECT(self, addr):
        val = self.get_mem(addr)
        if val == -1:
            return -1

        err = self.set_acc(self.ACC ^ val)
        if err != 0:
            return -1
        return 0

    def LSL(self, val):
        err = self.set_acc(self.ACC << val)
        if err != 0:
            return -1
        return 0

    def LSR(self, val):
        err = self.set_acc(self.ACC >> val)
        if err != 0:
            return -1
        return 0

    def OUT(self):
        ch = ''
        try:
            ch = chr(self.ACC)
            self.OUTPUT = ch
            self.print_program_output(ch)
        except Exception:
            return -1
        return 0

    def IN(self):
        try:
            a = _Getch()
            getch = a.__call__()

            self.set_acc(ord(getch))

            if not self.tracetable:
                print(getch, end='')

        except Exception:

            return -1
        return 0


    # System

    def parse_flags(self) -> int:

        parsing_data = False

        for i in range(len(self.tree)):
            instruction = self.tree[i]
            if instruction[0].endswith(':'):
                if len(instruction[0]) <= 1:
                    self.throw_syntax_error(f"flag name must have at least 1 character")
                    return 1

                flagname = instruction[0][0:len(instruction[0]) - 1]

                if len(instruction) < 2:
                    self.data_flags[flagname] = i

                    del self.tree[i][0]

                    continue

                if self.is_valid_opcode(instruction[1]):
                    self.code_flags[flagname] = i                                   # If it contains an opcode save the flag as an instruction

                    self.debug(f"set new source flag <{flagname}>: at instruction : {i}")

                    del self.tree[i][0]

                else:
                    if len(instruction) >= 2:
                        if len(instruction) > 2:
                            self.throw_syntax_error(f"too many arguments at data location {i} : {' '.join(instruction)}")
                            return 2
                        data = self.parse_byte_representation(instruction[1])
                        if data == -1:
                            self.throw_syntax_error(f"invalid byte at position {i} : {' '.join(instruction)}")
                            return 3
                        err = self.set_mem(i, data)
                        if err != 0:
                            return 4

                        parsing_data = True

                    self.data_flags[flagname] = i                                   # If instruction stores data send to data flags

                    self.debug(f"set new data flag <{flagname}>: at address : {i}")

                    for j in range(len(self.tree[i])):
                        del self.tree[i][j - 1]



            else:
                if parsing_data:
                    data = self.parse_byte_representation(instruction[0])
                    if data == -1:
                        if instruction[0].startswith('#') or instruction[0].startswith('&') or instruction[0].startswith('B'):
                            self.throw_syntax_error(f"invalid byte at position {i} : {' '.join(instruction)}")

                        parsing_data = False
                        continue
                    else:
                        err = self.set_mem(i, data)
                        if err != 0:
                            return 5

                        del self.tree[i][0]

        return 0


    def initialize_memory(self):
        self.MEM = []
        for i in range(self.MAX_ADDRESS):
            self.MEM.append(0)
        self.debug(f"initialized memory with size {self.MAX_ADDRESS}")

    def set_mem(self, position, data: int):
        if position >= len(self.MEM):
            self.throw_runtime_error(f"invalid mem position : {position} ; maximum is at : {len(self.MEM) - 1}")
            return 1
        elif position < 0:
            self.throw_syntax_error(f"invalid mem position : {position} ; mem position cannot be negative")
            return 1

        if data > (2 ** self.ARCH):
            self.throw_runtime_error(f"invalid data to write to memory ; maximum supported architecture is x{self.ARCH} ; provided data : {data}")
            return 1

        if not isinstance(data, int):
            self.throw_syntax_error(f"invalid data provided ; needed int : {data}")
            return 1

        self.MEM[position] = data

        return 0

    def get_mem(self, position):
        if position >= len(self.MEM):
            self.throw_runtime_error(f"invalid mem position : {position} ; maximum is at : {len(self.MEM) - 1}")
            return -1
        elif position < 0:
            self.throw_syntax_error(f"invalid mem position : {position} ; mem position cannot be negative")
            return -1

        return self.MEM[position]

    def parse_byte_representation(self, byte):
        if len(byte) < 2:
            return -1

        val = 0

        try:
            if byte.startswith('#'):
                val = int(byte[1:len(byte)])
            elif byte.startswith('&'):
                val = int(byte[1:len(byte)], base=16)
            elif byte.startswith('B'):
                val = int(byte[1:len(byte)], base=2)
            else:
                return -1

            if val > (2 ** self.ARCH):
                self.throw_runtime_error(f"byte exceeds architecture max size : {byte}")
                return -1

            return val

        except ValueError:
            return -1

    def parse_data_address(self, addr):
        try:
            addr = int(addr)
            if not self.is_valid_address(addr) or addr < 0 or addr >= len(self.MEM):
                self.throw_runtime_error(f"invalid address : {addr}")
                return -1
            return addr

        except ValueError:
            try:
                if addr in self.data_flags:
                    num = self.data_flags.get(addr)
                    return num
                return -1
            except (IndexError, KeyError):
                self.throw_runtime_error(f"invalid address : {addr}")
                return -1
        return -1

    def parse_code_address(self, addr):
        try:
            addr = int(addr)
            return addr

        except ValueError:
            try:
                if addr in self.code_flags:
                    num = self.code_flags.get(addr)
                    return num
                return -1
            except (IndexError, KeyError):
                self.throw_runtime_error(f"invalid instruction : {addr}")
                return -1
        return -1


    def is_valid_address(self, addr):
        if addr < 0 or addr >= len(self.MEM):
            return False
        return True

    def is_valid_opcode(self, opcode):
        if opcode.upper() in self.valid_opcodes:
            return True
        return False

    def load_source(self, source):
        self.source = source

    def throw_syntax_error(self, error):
        print(f"\033[38;5;1merror:\033[m {error}")

    def throw_runtime_error(self, error):
        print(f"\033[38;5;1merror:\033[m {error}")

    def debug(self, text):
        if self.DEBUG:
            print(f"\033[38;5;5mdebug:\033[m {text}")

    def print_value(self, name, value):
        print(f"\033[38;5;242m{name}\033[m {value}")

    def print_instruction(self, number, instruction):
        print(f"\033[38;5;9m{number}  :\033[m ", end = '')
        print(f"\033[38;5;12m{instruction[0]}\033[m ", end = '')
        if len(instruction) < 2:
            print()
            return
        print(f"\033[38;5;14m{instruction[1]}\033[m")

    def print_head_tracetable_line(self):

        count = 0
        for key, value in self.code_flags.items():
            count += 1

        if len(self.tree) < 10: l = 2
        elif len(self.tree) >= 10 and len(self.tree) < 100: l = 3
        elif len(self.tree) >= 100 and len(self.tree) < 1000: l = 4
        else: l = 5

        total = 42 + l

        a = ""
        b = ""
        g = ""

        for _ in range(total + 1): a += '-'
        for _ in range(l - 2): b += ' '

        if count > 0:
            for _ in range(19): a += '-'
            for _ in range(13): g += ' '

        print(f" {a} ")
        print(f" |  n  | instruction    {g}     | ACC | IX  | PC{b}| OUT |")
        print(f" {a} ")

    def print_tail_tracetable_line(self):

        count = 0
        for key, value in self.code_flags.items():
            count += 1

        if len(self.tree) < 10: l = 2
        elif len(self.tree) >= 10 and len(self.tree) < 100: l = 3
        elif len(self.tree) >= 100 and len(self.tree) < 1000: l = 4
        else: l = 5

        total = 42 + l

        if count > 0:
            total += 19

        a = ""

        for _ in range(total + 1): a += '-'

        print(f" {a} ")

    def print_tracetable_frame(self, number, instruction, pc, acc, ix, output):
        #for _ in range(len(' '.join(instruction))): print('-', end='')

        count = 0
        name = ""

        for key, value in self.code_flags.items():
            count += 1
            if value == pc:
                name = key

        if len(self.tree) < 10: l = 2
        elif len(self.tree) >= 10 and len(self.tree) < 100: l = 3
        elif len(self.tree) >= 100 and len(self.tree) < 1000: l = 4
        else: l = 5

        m = ""
        n = ""
        o = ""
        p = ""
        q = ""
        r = ""
        s = ""

        for _ in range(20 - len('  '.join(instruction))): n += ' '

        for _ in range(l - len(str(pc))): q += ' '
        for _ in range(4 - len(str(acc))): o += ' '
        for _ in range(4 - len(str(ix))): p += ' '
        for _ in range(4 - len(str(number))): m += ' '

        for _ in range(12 - len(name)): r += ' '

        if output == '':
            s = ' '

        #print(f">| {number}{m}| {' '.join(instruction)}{n}| {acc}{o}| {ix}{p}| {pc}{q}|", end="\r")
        #time.sleep(self.DELAY)

        if count > 0:
            if name != "":
                if len(instruction) >= 2:
                    print(f" | {number}{m}| {name}:{r}{' '.join(instruction)}{n} | {acc}{o}| {ix}{p}| {pc}{q}|  {output}{s}  |")
                else:
                    print(f" | {number}{m}| {name}:{r}{instruction[0]}{n}| {acc}{o}| {ix}{p}| {pc}{q}|  {output}{s}   |")
            else:
                if len(instruction) >= 2:
                    print(f" | {number}{m}|  {r}{' '.join(instruction)}{n} | {acc}{o}| {ix}{p}| {pc}{q}|  {output}{s}  |")
                else:
                    print(f" | {number}{m}|  {r}{instruction[0]}{n}| {acc}{o}| {ix}{p}| {pc}{q}|  {output}{s}  |")
        else:
            if len(instruction) >= 2:
                print(f" | {number}{m}|  {r}{' '.join(instruction)}{n} | {acc}{o}| {ix}{p}| {pc}{q}|  {output}{s}  |")
            else:
                print(f" | {number}{m}|  {r}{instruction[0]}{n}| {acc}{o}| {ix}{p}| {pc}{q}|  {output}{s}   |")

    def print_program_output(self, text):
        if not self.tracetable:
            print(text)
        return 0

    def set_debug(self, value):
        self.DEBUG = value
        self.debug("enabled debugging")

    def set_step(self, value):
        self.step = value
        self.debug(f"set stepping to : {value}")

    def set_tracetable(self, value):
        self.tracetable = value
        self.debug(f"set tracetable to : {value}")

    def set_show_acc(self, value):
        self.show_acc = value
        self.debug(f"set show ACC to : {value}")

    def set_show_ix(self, value):
        self.show_ix = value
        self.debug(f"set show IX to : {value}")

    def set_show_pc(self, value):
        self.show_pc = value
        self.debug(f"set show PC to : {value}")

    def set_show_inst(self, value):
        self.show_inst = value
        self.debug(f"set show instruction to : {value}")

    def set_interrupt(self, value):
        if value < 0 or value > (2 ** self.ARCH):
            self.throw_runtime_error(f"invalid interrupt value : {value}")
            return -1
        self.interrupt = value
        self.debug(f"set interrupt to : {value}")
        return 0

    # EFLAGS
    # Eflags contains a series of flags (not all are used in this program) wich are used by the virtual
    # machine to keep track of logical operations such as cmp's
    # For the implementation of this virtual machine, EFLAGS with bitmasking is unneccesary, but it was implemented
    # anyways for scalability and faithfullness to the x86 architecture

    # bit 1 -> ZF flag which stores result of CMP

    def get_eflags(self, bit):
        if bit > 7 or bit < 0:
            return -1

        mask = 2 ** bit                                 # bitmask to get bit n of byte

        ret = self.EFLAGS & mask                        # Apply the bitmask

        if ret > 0:
            return 1
        return 0

    def set_eflags(self, bit, value):
        if bit > 7 or bit < 0:
            return -1

        mask = 2 ** bit                                 # Same bitmaskt to obtain bit n

        if value == 1:
            self.EFLAGS = mask | self.EFLAGS            # Use OR to set bit to 1
        elif value == 0:
            self.EFLAGS = ~(mask) & self.EFLAGS         # Use AND against inverted bitmask to set bit to 0
        else:
            return -1

        return 0

    def set_pc(self, value):
        if value < 0:
            self.throw_runtime_error(f"value for PC cannot be lower than 0 : {value}")
            return -1
        elif value >= 2 ** self.ARCH:
            self.throw_runtime_error(f"value for PC cannot be greater than {2 ** self.ARCH} : {value}")
            return -1

        self.PC = value
        return 0

    def set_ix(self, value):
        if value < 0:
            self.IX = 0
            return -1
        elif value >= 2 ** self.ARCH:
            self.IX = (2 ** self.ARCH) - 1
            return -1
        self.IX = value
        return 0

    def set_acc(self, value):
        if value < 0:
            self.ACC = 0
            #return -1
        elif value >= 2 ** self.ARCH:
            self.ACC = (2 ** self.ARCH) - 1
            return -1
        self.ACC = value
        return 0

# Getch to read characters from stdin

class _Getch:
    #Gets a single character from standard input.  Does not echo to the screen
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()



if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print('''usage: asmvm [flags] <sourcefile.s>
flags:
\t--instruction\tshow each instruction after each clock_cycles
\t-d, --debug  \tenable real time debugging
\t-s, --step   \twait for a predefined time after each cycle
\t-t, --table  \tdraw a complete trace table for the program - not compatible with other representations
\t--acc        \tshow accumulator status after each cycle
\t--ix         \tshow index register status after each cycle
\t--pc         \tshow program counter status after each cycle
''')
        exit(0)

    source = ""

    if os.path.isfile(sys.argv[len(sys.argv) - 1]):
        try:
            with open(sys.argv[len(sys.argv) - 1], 'r') as file:
                source = file.read()
                file.close()
        except Exception as err:
            print(f"error: could not open file: {err}")
            exit(1)

    else:
        print(f"file does not exist : {sys.argv[1]}")
        exit(1)

    VM = VirtualMachine()

    if len(sys.argv) > 2:
        flags = sys.argv[1:len(sys.argv) - 1]
        for f in flags:
            if not f.startswith('-'):
                print(f"error: invalid flag : {f}")
                exit(1)
        for f in flags:
            if f == "-d" or f == "--debug":
                VM.set_debug(True)
            elif f == "-s" or f == "--step":
                VM.set_step(True)
            elif f == "-t" or f == "--table":
                VM.set_tracetable(True)
            elif f == "--acc":
                VM.set_show_acc(True)
            elif f == "--ix":
                VM.set_show_ix(True)
            elif f == "--pc":
                VM.set_show_pc(True)
            elif f == "--instruction":
                VM.set_show_inst(True)
            else:
                print(f"error: invalid flag : {f}")
                exit(1)

    try:

        VM.load_source(source)
        VM.run()

    except KeyboardInterrupt:

        VM.interrupt = 9                                                # Aborted by User
        print(f"\n * Clock cycles completed : {VM.clock_cycles}")       # Display clock cycles
        print("exiting...")

    except Exception as err:
        print(f"uncaught exception: {err}")
        exit(1)
        
