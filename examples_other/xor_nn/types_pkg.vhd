library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package types_pkg is
    constant Q : integer := 8; -- Q8.8
    subtype q8_8 is signed(15 downto 0); -- fixed point Q8.8
    type vec2 is array (0 to 1) of q8_8;
end package;
