library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.minicalc_datatypes.all;

entity minicalc is
  generic (
    N : integer := 8  -- Operand size
  );
  port (
    op_a      : in  signed (N-1 downto 0);
    op_b      : in  signed (N-1 downto 0);
    op        : in  op_type;
    op_valid  : in  std_ulogic;
    res       : out signed (2*N-1 downto 0);
    res_valid : out std_ulogic
  );
end minicalc;

architecture minicalc_arch of minicalc is

begin

  res_valid <= op_valid;

  comb: process(op_a, op_b, op)
  begin
    case op is
      when sum =>
        res <= op_a + op_b;
      when sub =>
        res <= op_a - op_b;
      when mul =>
        res <= op_a * op_b;
    end case;
  end process;

end minicalc_arch;
