library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.olo_base_pkg_math.all;

package fifo_sync_common is

    constant Width_g : integer := 8;
    constant Depth_g : integer := 8;

    type input_tran_in_data is record
        data : std_logic_vector(Width_g - 1 downto 0);
        level: std_logic_vector(log2ceil(Depth_g + 1) - 1 downto 0);  
    end record;

end package fifo_sync_common;

package body fifo_sync_common is

end package body fifo_sync_common;
