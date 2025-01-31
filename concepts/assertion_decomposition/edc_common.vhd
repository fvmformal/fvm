-- @author Hipólito Guzmán-Miranda
-- Define fixed-point complex datatypes of different widths
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package edc_common is

    -- Complex fixed-point number with 10 bits per component
    type complex10 is
        record
            re : signed(9 downto 0);
            im : signed(9 downto 0);
        end record;

    -- Complex fixed-point number with 15 bits per component
    type complex15 is
        record
            re : signed(14 downto 0);
            im : signed(14 downto 0);
        end record;

end edc_common;

package body edc_common is

end edc_common;
