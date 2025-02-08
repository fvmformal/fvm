library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library gaisler;
use gaisler.arith.all;

package div32_common is
    function verify_division(
        y    : std_logic_vector(32 downto 0);
        op1  : std_logic_vector(32 downto 0);
        op2  : std_logic_vector(32 downto 0)
    ) return std_logic_vector;
end package div32_common;

package body div32_common is
    function verify_division(
        y    : std_logic_vector(32 downto 0);
        op1  : std_logic_vector(32 downto 0);
        op2  : std_logic_vector(32 downto 0)
    ) return std_logic_vector is
        variable dividend  : unsigned(63 downto 0);
        variable divisor   : unsigned(31 downto 0);
        variable quotient  : unsigned(63 downto 0);  
    begin
        dividend := unsigned(y(31 downto 0) & op1(31 downto 0));  
        divisor  := unsigned(op2(31 downto 0)); 
        
        quotient := dividend / divisor;
        
        return std_logic_vector(quotient(31 downto 0)); 
    end function verify_division;
end package body div32_common;

