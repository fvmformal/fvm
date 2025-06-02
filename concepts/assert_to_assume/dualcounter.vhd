library IEEE;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

entity dualcounter is
  generic (MAX_COUNT : integer := 200);
  port (
    rst      : in  std_logic;
    clk      : in  std_logic;
    equalmsb : out std_logic
    );
end dualcounter;

architecture Behavioral of dualcounter is

  signal count0 : unsigned(integer(ceil(log2(real(MAX_COUNT))))-1 downto 0);
  signal count1 : unsigned(integer(ceil(log2(real(MAX_COUNT))))-1 downto 0);

  -- Necesito declararlo para poderlo usar, pero el hecho de declararlo no
  -- significa que lo esté usando ni me obliga a usarlo
  component counter is
    generic ( MAX_COUNT : integer := 100 );
    port ( clk: in  std_logic;
           rst: in  std_logic;
           Q:   out unsigned(integer(ceil(log2(real(MAX_COUNT))))-1 downto 0)
         );
  end component;

begin

  -- Quiero poner DOS copias del contador
  -- cada una ocupará los recursos correspondientes a un contador

  -- Primera copia (instancia en VHDL)
  counter0 : counter
    generic map (MAX_COUNT => MAX_COUNT)
    port map(rst => rst,
             clk => clk,
             Q   => count0);

  -- Segunda copia (segunda instancia)
  counter1 : counter
    generic map (MAX_COUNT => MAX_COUNT)
    port map(rst => rst,
             clk => clk,
             Q   => count1);

  equalmsb <= '1' when (count0(count0'high) = count1(count1'high)) else '0';

end Behavioral;
