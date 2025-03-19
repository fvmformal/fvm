-- Linearly interpolates between inferior and superior, outputting 12 intermediate values
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.edc_common.all;
use work.interpolator_common.all;

entity interpolator is
        port (
            clk : in std_logic;          -- Input clock, active on rising edge
            rst : in std_logic;          -- Asynchronous reset, active high
            inferior : in complex10;     -- Low input
            superior : in complex10;     -- High input
            valid : in std_logic;        -- When ``'1'``, signals the interpolator to begin interpolating between ``inferior`` and ``superior``
            estim : out complex10;       -- Interpolated output. Has a 12/16 scale factor, since it estimates 12 times the channel and discards 4 LSB
            estim_valid : out std_logic  -- Takes the value ``'1'`` when ``estim`` is valid
        );
    end interpolator;

architecture interpolator_arch of interpolator is

    signal i, n_i    : unsigned (3 downto 0);  -- Current interpolation stage
    signal estim_aux : complex15;              -- Result of the interpolation, before discarding the LSB

    -- Two signals needed for the firewall assertions
    -- signal firewall_inferior, firewall_superior : complex10;

begin

    sinc: process(rst, clk)
    begin
        if rst = '1' then
            i <= to_unsigned(12,i'length);  -- set i to 12
        elsif rising_edge(clk) then
            i <= n_i;
        end if;
    end process;

    -- i controls the interpolation:
    -- when i = 12 we are idle
    -- if we receive a valid input, we go to i = 0
    -- when i is between 0 and 11, interpolate
    -- afterwards go again to i = 12
    comb: process(inferior, superior, valid, i)
    begin
        if i > 11 then  -- Anything that is not between 0 and 11: idle
            estim_valid <= '0';
            if valid = '1' then
                n_i <= to_unsigned(0, n_i'length);
            else
                n_i <= to_unsigned(12,n_i'length);
            end if;
        else                         -- Between 0 and 11: interpolate
            n_i <= i + 1;
            estim_valid <= '1';
            estim_aux.re <= inferior.re*(12-signed(resize(i, i'length+1))) + superior.re*signed(resize(i, i'length+1));
            estim_aux.im <= inferior.im*(12-signed(resize(i, i'length+1))) + superior.im*signed(resize(i, i'length+1));
        end if;
    end process;

    -- Discard the most significant bit since it doesn't contain any
    -- information (it is redundant with bit 13), and keep the 10 most
    -- significant of the rest
    estim.re <= estim_aux.re(13 downto 4);
    estim.im <= estim_aux.im(13 downto 4);

    -- Firewall assertions have been commented out because the
    -- falling_edge(clk) here messes with how Questa PropCheck counts cycles
    -- (since our default clock in PSL is rising_edge(clk))
    --
    -- Firewall assertions: assure that our module is being used correctly
    --
    -- What can go wrong?
    --
    -- 1) Valid cannot be asserted while the interpolator is busy
    --
    -- 2) Input data cannot change while the interpolator is busy
    -- (the interpolator is busy if 0 <= i <= 11)
    --
    -- An interesting idea here would be to define a procedure in
    -- edc_common.vhd called "fail_in_N_cycles", which would
    -- wait N clock cycles before stopping the simulation
    --firewall_assertions: process (clk)
    --begin
    --    if falling_edge(clk) then
    --        firewall_superior <= superior;
    --        firewall_inferior <= inferior;
    --        if (i >= 0) and (i <= 11) then
    --            if valid = '1' then
    --                report "valid asserted while interpolator busy, data will be lost"
    --                severity failure;
    --            end if;
    --            if (inferior /= firewall_inferior) or (superior /= firewall_superior) then
    --                report "data changed while interpolator busy, interpolation will be wrong"
    --                severity failure;
    --            end if;
    --        end if;
    --    end if;
    --end process;

end interpolator_arch;
