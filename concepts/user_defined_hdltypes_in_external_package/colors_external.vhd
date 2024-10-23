-- This package will not be included from the synthesizable design, just from
-- the PSL properties
library ieee;
use ieee.std_logic_1164.all;
use work.colors_common.all;

package colors_external is

  type color_record is
    record
      a : color_t;
      b : color_t;
      c : color_t;
    end record;

end package;

package body colors_external is

end package body;
