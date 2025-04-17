library IEEE;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity counter is
    generic ( MAX_COUNT : integer := 128 );
    port ( clk: in  std_logic;
           rst: in  std_logic;
           Q:   out unsigned(7 downto 0)
         );
end counter;

architecture behavioral of counter is

    signal r_count:   unsigned(7 downto 0);
    signal rin_count: unsigned(7 downto 0);

begin

    sinc: process(clk, rst)
    begin
      if (rst='1') then
        r_count <= (others=>'0');
      elsif (rising_edge(clk)) then
        r_count <= rin_count;
      end if;
    end process;

    comb: process(r_count)
      variable v_count: unsigned(7 downto 0);
    begin
      if (r_count = MAX_COUNT) then
	      v_count := (others => '0');
      else
	      v_count := r_count + 1;
      end if;
      rin_count <= v_count;
    end process;

    Q <= r_count;

end behavioral;
