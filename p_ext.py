from cocotb.binary import BinaryValue
from cocotb_coverage.coverage import *
import os
import sys
import operator
from cocotb.result import ReturnValue
import logging as log

#from constants import *

if(True)
    print("HELLO")


# Define Coverage for ADD16 and RADD16
bitmanip_Coverage = coverage_section (
         CoverPoint("bitmanip_model.EN_mav_putvalue", xf = lambda mav_putvalue_instr, mav_putvalue_src1, mav_putvalue_src2, mav_putvalue_src3, EN_mav_putvalue : EN_mav_putvalue, bins=[0, 1]),
         CoverPoint("bitmanip_model.instruction___RTYPE", xf = lambda mav_putvalue_instr, mav_putvalue_src1, mav_putvalue_src2, mav_putvalue_src3, EN_mav_putvalue : (mav_putvalue_instr & 0x7F), bins=[0x33]),
         CoverPoint("bitmanip_model.instruction___func3", xf = lambda mav_putvalue_instr, mav_putvalue_src1, mav_putvalue_src2, mav_putvalue_src3, EN_mav_putvalue : ((mav_putvalue_instr >> 12) & 0x7), bins=list(range(0, 0x8))),
         CoverPoint("bitmanip_model.instruction___func7", xf = lambda mav_putvalue_instr, mav_putvalue_src1, mav_putvalue_src2, mav_putvalue_src3, EN_mav_putvalue : ((mav_putvalue_instr >> 25) & 0x7F), bins=[0x00, 0x01]),
         CoverCross("bitmanip_model.covercross_RTYPE", items=["bitmanip_model.instruction___RTYPE", "bitmanip_model.instruction___func3", "bitmanip_model.instruction___func7"])
)

@bitmanip_Coverage
def bitmanip(mav_putvalue_instr, mav_putvalue_src1, mav_putvalue_src2, mav_putvalue_src3, EN_mav_putvalue):
    instr = hex(mav_putvalue_instr)[2:]
    le = int(instr, 16)  # Convert Hex to int
    le = bin(le)[2:]  # Convert int to binary
    le = le.zfill(32)  # Ensure it's 32 bits

    opcode = le[-7:]  # Extract opcode (bits 6 to 0)
    func3 = le[-15:-12]  # Extract func3 (bits 14 to 12)
    func7 = le[-32:-25]  # Extract func7 (bits 31 to 25)

    # ADD16 (0000000) or RADD16 (0000001) Detection
    if opcode == "1110111" and func3 == "000":
        if func7 == "0000000":  # ADD16
            return add16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0000001":  # RADD16
            return radd16(mav_putvalue_src1, mav_putvalue_src2)

def add16(rs1, rs2):
    """
    ADD16 Instruction: Adds 16-bit elements from Rs1 and Rs2 in parallel.
    For RV32: x = 1..0
    For RV64: x = 3..0
    """
    result = 0
    for x in range(4):  # Loop over 4 half-word elements for RV64, or 2 for RV32
        rs1_half = (rs1 >> (x * 16)) & 0xFFFF  # Extract 16-bit segment from Rs1
        rs2_half = (rs2 >> (x * 16)) & 0xFFFF  # Extract 16-bit segment from Rs2

        # Perform unsigned or signed addition
        rd_half = (rs1_half + rs2_half) & 0xFFFF  # Mask to ensure 16 bits

        # Combine result into the appropriate position in the final result
        result |= (rd_half << (x * 16))
    
    return result

def radd16(rs1, rs2):
    """
    RADD16 Instruction: Adds 16-bit signed elements from Rs1 and Rs2 in parallel, then right-shifts the result by 1.
    For RV32: x = 1..0
    For RV64: x = 3..0
    """
    result = 0
    for x in range(4):  # Loop over 4 half-word elements for RV64, or 2 for RV32
        rs1_half = (rs1 >> (x * 16)) & 0xFFFF  # Extract 16-bit segment from Rs1
        rs2_half = (rs2 >> (x * 16)) & 0xFFFF  # Extract 16-bit segment from Rs2

        # Sign extend the 16-bit halves to 17 bits for addition
        rs1_signed = sign_extend_16_to_17(rs1_half)
        rs2_signed = sign_extend_16_to_17(rs2_half)

        # Perform signed addition and arithmetic right shift by 1
        rd_half = (rs1_signed + rs2_signed) >> 1

        # Mask to get the lower 16 bits after the shift
        rd_half = rd_half & 0xFFFF

        # Combine result into the appropriate position in the final result
        result |= (rd_half << (x * 16))
    
    return result

def sign_extend_16_to_17(value):
    """
    Sign extend a 16-bit value to 17-bit for addition.
    """
    if value & 0x8000:  # If the sign bit (bit 15) is 1
        return value | 0x10000  # Extend to 17-bit by setting the 17th bit
    else:
        return value
