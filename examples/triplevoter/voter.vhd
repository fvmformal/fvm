library IEEE;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity voter is
    port (
           input  : in std_logic_vector(2 downto 0);
           output : out std_logic
         );
end voter;

architecture voter_arch of voter is

begin

    output <= (input(0) AND input(1)) OR
              (input(0) AND input(2)) OR
              (input(1) AND input(2));

end voter_arch;
