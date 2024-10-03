library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.minicalc_datatypes.all;

entity minicalc is
  generic (
    N : integer := 8  -- Operand size
  );
  port (
    rst       : in  std_ulogic;
    clk       : in  std_ulogic;
    op_a      : in  signed (N-1 downto 0);
    op_b      : in  signed (N-1 downto 0);
    op        : in  op_type;
    op_valid  : in  std_ulogic;
    res       : out signed (2*N-1 downto 0);
    res_valid : out std_ulogic
  );
end minicalc;

architecture minicalc_arch of minicalc is

  signal n_res       : signed(2*N-1 downto 0);
  signal n_res_valid : std_ulogic;

begin

  n_res_valid <= op_valid;

  comb: process(op_a, op_b, op)
  begin
    case op is
      when sum =>
        n_res <= op_a + op_b;
      when sub =>
        n_res <= op_a - op_b;
      when mul =>
        n_res <= op_a * op_b;
    end case;
  end process;

  sync: process(rst, clk)
  begin
    if rst = '1' then
      res <= (others => '0');
      res_valid <= '0';
    elsif rising_edge(clk) then
      res <= n_res;
      res_valid <= n_res_valid;
    end if;
  end process;

end minicalc_arch;
