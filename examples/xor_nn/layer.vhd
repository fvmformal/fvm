library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.types_pkg.all;

entity layer is
    port (
        inputs : in  vec2;
        weights: in  vec2; 
        weights2: in vec2;
        bias1  : in  q8_8;
        bias2  : in  q8_8;
        outputs: out vec2
    );
end layer;

architecture rtl of layer is
    component neuron
        port (inputs, weights: in vec2; 
              bias: in q8_8; 
              output: out q8_8);
    end component;
begin
    n1: neuron 
      port map(inputs => inputs, 
               weights => weights, 
               bias => bias1, 
               output => outputs(0));
    n2: neuron 
      port map(inputs => inputs, 
               weights => weights2, 
               bias => bias2, 
               output => outputs(1));
end rtl;
