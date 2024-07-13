library IEEE;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity counter is
    generic ( MAX_COUNT : integer := 100 );
    port ( clk: in  std_logic;
           rst: in  std_logic;
           Q:   out unsigned(7 downto 0)
         );
end counter;

architecture behavioral of counter is

    signal count:   unsigned(7 downto 0);
    signal p_count: unsigned(7 downto 0);

begin


    -- Default clock for PSL assertions
    -- psl default clock is rising_edge(clk);

    -- Assert we do not go over the maximum
    -- psl never_go_over_the_maximum: assert always (Q <= MAX_COUNT);

    -- Assert the counter is always counting up, but only:
    -- 1) If it's not the first clock cycle
    -- 2) If it hasn't just been reset
    -- 3) If last value wasn't MAX_COUNT
    -- psl always_count_up: assert always (not (rst = '1') and (not prev(rst) = '1') and (prev(Q) /= MAX_COUNT)) -> (Q-prev(Q) = 1);

    -- Cover the overflow -> zero case
    -- What we write here has to be a sequence inside curly braces {}, even if
    -- we only have one element (for example, { Q = MAX_COUNT }
    -- psl cover_overflow_to_zero: cover {Q = MAX_COUNT ; Q = 0};

    -- Force a reset in the first clock cycle
    -- Since we don't have an 'always', this assumption only applies to the
    -- first clock cycle
    -- psl assume_initial_reset: assume rst = '1';


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
