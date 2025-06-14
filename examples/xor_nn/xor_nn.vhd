library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.types_pkg.all;

entity xor_nn is
    port (
        x1, x2   : in  std_logic;
        y: out std_logic
    );
end xor_nn;

architecture rtl of xor_nn is
    component layer
        port (
            inputs: in vec2;
            weights, weights2: in vec2;
            bias1, bias2: in q8_8;
            outputs: out vec2
        );
    end component;

    component neuron
        port (inputs, weights: in vec2; 
              bias: in q8_8; 
              output: out q8_8);
    end component;

    signal in_vec   : vec2;
    signal hidden   : vec2;
    signal out_raw  : q8_8;

    -- Trained weights (Q8.8 format)
    constant w1 : vec2 := (to_signed(1371,16), to_signed(1365,16));   -- 5.3543396, 5.3326964 (neuron 1 weights)
    constant w2 : vec2 := (to_signed(-2086,16), to_signed(-1988,16));   -- -8.147653 , -7.767397 (neuron 2 weights)
    constant b1 : q8_8 := to_signed(-2014,16); -- -7.8683677 (neuron 1 bias)
    constant b2 : q8_8 := to_signed(856,16); -- 3.345057 (neuron 2 bias)

    constant w_out : vec2 := (to_signed(-2025,16), to_signed(-2185,16)); -- -7.9095736, -8.53574 (output layer weights)
    constant b_out : q8_8 := to_signed(1079,16); -- 4.215635 (output bias)

begin
    -- Input
    in_vec(0) <= to_signed(256, 16) when x1 = '1' else to_signed(0, 16);
    in_vec(1) <= to_signed(256, 16) when x2 = '1' else to_signed(0, 16);

    -- Layers
    l1: layer 
      port map(inputs => in_vec,
               weights => w1, 
               weights2 => w2, 
               bias1 => b1, 
               bias2 => b2, 
               outputs => hidden);

    l2: neuron 
      port map(inputs => hidden, 
               weights => w_out, 
               bias => b_out, 
               output => out_raw);

    -- Output
    y <= '1' when out_raw > to_signed(128, 16) else '0'; -- threshold -> 0.5
end rtl;
