from cocotb.binary import BinaryValue
from cocotb_coverage.coverage import *
import os
import sys
import operator
from cocotb.result import ReturnValue
import logging as log

#from constants import *
# NNN,NameError


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
        elif func7 == "0010000":  # URADD16
            return uradd16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0001000":  # KADD16
            return kadd16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0011000":  # UKADD16
            return ukadd16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0100001":  # SUB16
            return sub16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0000001":  # RSUB16
            return rsub16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0010001":  # URSUB16
            return ursub16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0001001":  # KSUB16
            return ksub16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0011001":  # UKSUB16
            return uksub16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0100010":  # CRAS16
            return uksub16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0000010":  # RCRAS16
            return uksub16(mav_putvalue_src1, mav_putvalue_src2)
        elif func7 == "0010010":  # URCRAS16
            return uksub16(mav_putvalue_src1, mav_putvalue_src2)

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

def uradd16(rs1, rs2):
    """
    URADD16 Instruction: Adds 16-bit unsigned elements from Rs1 and Rs2 in parallel.
    The results are right-shifted by 1 before being written to Rd.
    For RV32: x = 1..0
    For RV64: x = 3..0
    """
    result = 0
    for x in range(4):  # Loop over 4 half-word elements for RV64, or 2 for RV32
        rs1_half = (rs1 >> (x * 16)) & 0xFFFF  # Extract 16-bit segment from Rs1
        rs2_half = (rs2 >> (x * 16)) & 0xFFFF  # Extract 16-bit segment from Rs2

        # Perform unsigned addition
        sum_half = (rs1_half + rs2_half) & 0x1FFFF  # Mask to 17 bits for overflow checking

        # Right shift the result by 1 to obtain final value
        rd_half = sum_half >> 1  # This can safely handle both 16-bit and 17-bit results

        # Mask to get the lower 16 bits after the shift
        rd_half = rd_half & 0xFFFF

        # Combine result into the appropriate position in the final result
        result |= (rd_half << (x * 16))

    return result

def kadd16(rs1, rs2):
    """
    KADD16 Instruction: Adds 16-bit signed elements from Rs1 and Rs2 in parallel with saturation.
    If the result exceeds the Q15 range (-32768 to 32767), it saturates the value.
    For RV32: x = 1..0
    For RV64: x = 3..0
    """
    OV = 0  # Overflow flag
    result = 0

    for x in range(4):  # Loop over 4 half-word elements for RV64, or 2 for RV32
        rs1_half = (rs1 >> (x * 16)) & 0xFFFF  # Extract 16-bit segment from Rs1
        rs2_half = (rs2 >> (x * 16)) & 0xFFFF  # Extract 16-bit segment from Rs2

        # Sign extend the 16-bit halves to 17 bits
        a17 = sign_extend_16_to_17(rs1_half)
        b17 = sign_extend_16_to_17(rs2_half)

        # Perform signed addition
        res17 = a17 + b17

        # Saturation logic for Q15 range (-32768 to 32767)
        if res17 > 32767:
            res17 = 32767
            OV = 1
        elif res17 < -32768:
            res17 = -32768
            OV = 1

        # Combine the result into the appropriate position in the final result
        result |= (res17 & 0xFFFF) << (x * 16)
    
    return result, OV

def ukadd16(rs1, rs2):
    """
    UKADD16 Instruction: Adds 16-bit unsigned elements from Rs1 and Rs2 in parallel with saturation.
    If the result exceeds the 16-bit unsigned range (0 to 65535), it saturates the value.
    For RV32: x = 1..0
    For RV64: x = 3..0
    """
    OV = 0  # Overflow flag
    result = 0

    for x in range(4):  # Loop over 4 half-word elements for RV64, or 2 for RV32
        rs1_half = (rs1 >> (x * 16)) & 0xFFFF  # Extract 16-bit segment from Rs1
        rs2_half = (rs2 >> (x * 16)) & 0xFFFF  # Extract 16-bit segment from Rs2

        # Perform unsigned addition
        res = rs1_half + rs2_half

        # Saturation logic for 16-bit unsigned range (0 to 65535)
        if res > 0xFFFF:  # 65535 is the maximum 16-bit unsigned value
            res = 0xFFFF  # Saturate to maximum
            OV = 1  # Set the overflow flag

        # Combine the result into the appropriate position in the final result
        result |= (res & 0xFFFF) << (x * 16)
    
    return result, OV

def sub16(rs1, rs2):
    """
    SUB16 Instruction: Subtracts 16-bit elements from Rs2 from Rs1 in parallel.
    Works for both RV32 (x=1..0) and RV64 (x=3..0).
    """
    result = 0

    # Loop over 4 half-word elements for RV64, or 2 for RV32
    for x in range(4):  # Adjust loop for 2 iterations for RV32 if required
        # Extract 16-bit segments from Rs1 and Rs2
        rs1_half = (rs1 >> (x * 16)) & 0xFFFF
        rs2_half = (rs2 >> (x * 16)) & 0xFFFF

        # Perform signed or unsigned subtraction
        rd_half = rs1_half - rs2_half

        # Mask to ensure the result is 16-bit
        rd_half = rd_half & 0xFFFF

        # Combine the result into the appropriate position in the final result
        result |= (rd_half << (x * 16))
    
    return result


def rsub16(rs1, rs2):
    """
    RSUB16 Instruction: Subtracts 16-bit signed elements of Rs2 from Rs1 in parallel,
    and then performs an arithmetic right shift by 1 to avoid overflow.
    Works for both RV32 (x=1..0) and RV64 (x=3..0).
    """
    result = 0

    # Loop over 4 half-word elements for RV64, or 2 for RV32
    for x in range(4):  # Adjust loop for 2 iterations for RV32 if required
        # Extract 16-bit segments from Rs1 and Rs2
        rs1_half = (rs1 >> (x * 16)) & 0xFFFF
        rs2_half = (rs2 >> (x * 16)) & 0xFFFF

        # Sign extend to 17 bits (to handle signed subtraction)
        rs1_signed = sign_extend_16_to_17(rs1_half)
        rs2_signed = sign_extend_16_to_17(rs2_half)

        # Perform signed subtraction
        res_signed = rs1_signed - rs2_signed

        # Perform arithmetic right shift by 1
        rd_half = res_signed >> 1

        # Mask the result to ensure it's 16 bits after the shift
        rd_half = rd_half & 0xFFFF

        # Combine the result into the appropriate position in the final result
        result |= (rd_half << (x * 16))

    return result

def ursub16(rs1, rs2):
    """
    URSUB16 Instruction: Subtracts 16-bit unsigned elements of Rs2 from Rs1 in parallel,
    and then performs an unsigned right shift by 1 to avoid overflow.
    Works for both RV32 (x=1..0) and RV64 (x=3..0).
    """
    result = 0

    # Loop over 4 half-word elements for RV64, or 2 for RV32
    for x in range(4):  # Adjust loop for 2 iterations for RV32 if required
        # Extract 16-bit segments from Rs1 and Rs2
        rs1_half = (rs1 >> (x * 16)) & 0xFFFF
        rs2_half = (rs2 >> (x * 16)) & 0xFFFF

        # Zero extend to 17 bits
        rs1_unsigned = rs1_half & 0xFFFF
        rs2_unsigned = rs2_half & 0xFFFF

        # Perform unsigned subtraction
        res_unsigned = rs1_unsigned - rs2_unsigned

        # Perform unsigned right shift by 1
        rd_half = (res_unsigned >> 1) & 0xFFFF

        # Combine the result into the appropriate position in the final result
        result |= (rd_half << (x * 16))

    return result

def ksub16(rs1, rs2):
    """
    KSUB16 Instruction: Subtracts 16-bit signed elements of Rs2 from Rs1 in parallel
    and saturates the results to the Q15 range (-2^15 <= Q15 <= 2^15-1).
    Works for both RV32 (x=1..0) and RV64 (x=3..0).
    
    Returns the saturated result.
    """
    result = 0

    # Loop over 4 half-word elements for RV64, or 2 for RV32
    for x in range(4):  # Adjust loop for 2 iterations for RV32 if required
        # Extract 16-bit signed segments from Rs1 and Rs2
        rs1_half = (rs1 >> (x * 16)) & 0xFFFF
        rs2_half = (rs2 >> (x * 16)) & 0xFFFF

        # Sign-extend to 17 bits for subtraction
        rs1_signed = sign_extend_16_to_17(rs1_half)
        rs2_signed = sign_extend_16_to_17(rs2_half)

        # Perform signed subtraction
        res_signed = rs1_signed - rs2_signed

        # Saturate the result to Q15 range
        if res_signed > 32767:  # Max positive value for Q15 (2^15 - 1)
            res_signed = 32767
        elif res_signed < -32768:  # Min negative value for Q15 (-2^15)
            res_signed = -32768

        # Mask the lower 16 bits to get the final result for this half-word
        rd_half = res_signed & 0xFFFF

        # Combine the result into the appropriate position in the final result
        result |= (rd_half << (x * 16))

    return result

def uksub16(rs1, rs2):
    """
    UKSUB16 Instruction: Subtracts 16-bit unsigned elements of Rs2 from Rs1 in parallel
    and saturates the results to the unsigned 16-bit range (0 ≤ result ≤ 65535).
    Works for both RV32 (x=1..0) and RV64 (x=3..0).
    
    Returns the saturated result.
    """
    result = 0
    overflow = 0

    # Loop over 4 half-word elements for RV64, or 2 for RV32
    for x in range(4):  # Adjust loop for 2 iterations for RV32 if required
        # Extract 16-bit unsigned segments from Rs1 and Rs2
        rs1_half = (rs1 >> (x * 16)) & 0xFFFF
        rs2_half = (rs2 >> (x * 16)) & 0xFFFF

        # Zero-extend to 17 bits for subtraction
        rs1_unsigned = zero_extend_16_to_17(rs1_half)
        rs2_unsigned = zero_extend_16_to_17(rs2_half)

        # Perform unsigned subtraction
        res_unsigned = rs1_unsigned - rs2_unsigned

        # Saturate the result if it goes below 0
        if res_unsigned < 0:
            res_unsigned = 0
            overflow = 1  # Overflow occurred

        # Mask the lower 16 bits to get the final result for this half-word
        rd_half = res_unsigned & 0xFFFF

        # Combine the result into the appropriate position in the final result
        result |= (rd_half << (x * 16))

    return result  

def cras16(rs1, rs2):
    """
    CRAS16 Instruction: Cross Addition and Subtraction for 16-bit elements.
    Adds [31:16] of Rs1 with [15:0] of Rs2, and subtracts [31:16] of Rs2 from [15:0] of Rs1.
    """
    result = 0
    for x in range(2):  # Loop over 32-bit chunks, x=0 for RV32, x=1..0 for RV64
        # Extract 16-bit elements
        rs1_upper = (rs1 >> (x * 32 + 16)) & 0xFFFF  # Rs1[31:16]
        rs1_lower = (rs1 >> (x * 32)) & 0xFFFF       # Rs1[15:0]
        rs2_upper = (rs2 >> (x * 32 + 16)) & 0xFFFF  # Rs2[31:16]
        rs2_lower = (rs2 >> (x * 32)) & 0xFFFF       # Rs2[15:0]

        # Perform cross addition and subtraction
        rd_upper = (rs1_upper + rs2_lower) & 0xFFFF  # Rd[31:16] = Rs1[31:16] + Rs2[15:0]
        rd_lower = (rs1_lower - rs2_upper) & 0xFFFF  # Rd[15:0] = Rs1[15:0] - Rs2[31:16]

        # Combine result for this 32-bit chunk
        result |= (rd_upper << (x * 32 + 16))  # Store in upper half of 32-bit chunk
        result |= (rd_lower << (x * 32))       # Store in lower half of 32-bit chunk

    return result

def rcras16(rs1, rs2):
    """
    RCRAS16 Instruction: Performs signed 16-bit integer element addition and subtraction in a 32-bit chunk.
    The results are halved and written to Rd.
    For RV32, x=0
    For RV64, x=1..0
    """
    result = 0
    for x in range(2):  # Loop over 32-bit chunks
        # Cross addition and subtraction with halving
        rs1_hi = sign_extend_16_to_17((rs1 >> (x * 32 + 16)) & 0xFFFF)  # Rs1.W[x].H[1]
        rs1_lo = sign_extend_16_to_17((rs1 >> (x * 32)) & 0xFFFF)  # Rs1.W[x].H[0]
        rs2_hi = sign_extend_16_to_17((rs2 >> (x * 32 + 16)) & 0xFFFF)  # Rs2.W[x].H[1]
        rs2_lo = sign_extend_16_to_17((rs2 >> (x * 32)) & 0xFFFF)  # Rs2.W[x].H[0]

        # Perform signed addition and subtraction with arithmetic right shift by 1
        res_add = (rs1_hi + rs2_lo) >> 1
        res_sub = (rs1_lo - rs2_hi) >> 1

        # Mask the result to 16 bits
        res_add &= 0xFFFF
        res_sub &= 0xFFFF

        # Combine the results into Rd
        result |= (res_add << (x * 32 + 16))  # Rd.W[x].H[1] = res_add
        result |= (res_sub << (x * 32))  # Rd.W[x].H[0] = res_sub

    return result

def urcras16(rs1, rs2):
    """
    URCRAS16 Instruction: Performs unsigned 16-bit integer element addition and subtraction in a 32-bit chunk.
    The results are halved and written to Rd.
    For RV32, x=0
    For RV64, x=1..0
    """
    result = 0
    for x in range(2):  # Loop over 32-bit chunks
        # Cross addition and subtraction with halving
        rs1_hi = (rs1 >> (x * 32 + 16)) & 0xFFFF  # Rs1.W[x].H[1]
        rs1_lo = (rs1 >> (x * 32)) & 0xFFFF  # Rs1.W[x].H[0]
        rs2_hi = (rs2 >> (x * 32 + 16)) & 0xFFFF  # Rs2.W[x].H[1]
        rs2_lo = (rs2 >> (x * 32)) & 0xFFFF  # Rs2.W[x].H[0]

        # Perform unsigned addition and subtraction with logical right shift by 1
        res_add = (rs1_hi + rs2_lo) >> 1
        res_sub = (rs1_lo - rs2_hi) >> 1

        # Mask the result to 16 bits
        res_add &= 0xFFFF
        res_sub &= 0xFFFF

        # Combine the results into Rd
        result |= (res_add << (x * 32 + 16))  # Rd.W[x].H[1] = res_add
        result |= (res_sub << (x * 32))  # Rd.W[x].H[0] = res_sub

    return result


def sign_extend_16_to_17(value):
    """
    Sign extend a 16-bit value to 17-bit for addition.
    """
    if value & 0x8000:  # If the sign bit (bit 15) is 1
        return value | 0x10000  # Extend to 17-bit by setting the 17th bit
    else:
        return value
    
def zero_extend_16_to_17(value):
    """
    Zero-extend a 16-bit value to 17 bits for unsigned subtraction.
    """
    return value & 0xFFFF  # Keep the value as a positive 16-bit value


print("---------------------EXECUTED SUCCESSFULLY-----------------------")