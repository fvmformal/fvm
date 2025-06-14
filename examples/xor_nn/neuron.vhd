library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.types_pkg.all;

entity neuron is
    port (
        inputs : in vec2;
        weights: in vec2;
        bias   : in q8_8;
        output : out q8_8
    );
end neuron;

architecture rtl of neuron is
    signal acc    : q8_8;
    signal preact : q8_8;

    component sigmoid is
        port (
            x : in  q8_8;
            y : out q8_8
        );
    end component;
begin

    activation_fn: sigmoid
        port map (
            x => preact,
            y => output
        );

    process(inputs, weights, bias)
        variable prod0, prod1: signed(31 downto 0);
        variable sum: signed(31 downto 0);
    begin
        prod0 := resize(signed(inputs(0)) * signed(weights(0)), 32);
        prod1 := resize(signed(inputs(1)) * signed(weights(1)), 32);
        sum := prod0 + prod1 + (resize(signed(bias), 32) sll 8); -- Q8.8 bias → Q16.16

        preact <= sum(23 downto 8) + sum(7); -- Basic rounding
    end process;
end rtl;
