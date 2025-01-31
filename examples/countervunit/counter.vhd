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

    signal count:   unsigned(7 downto 0);
    signal p_count: unsigned(7 downto 0);

begin

    sinc: process(clk, rst)
    begin
      if (rst='1') then
        count <= (others=>'0');
      elsif (rising_edge(clk)) then
        count <= p_count;
      end if;
    end process;

    comb: process(count)
    begin
      if (count = MAX_COUNT) then
	p_count <= (others => '0');
      else
	p_count <= count + 1;
      end if;
    end process;

    Q <= count;

end behavioral;
