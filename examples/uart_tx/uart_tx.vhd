library ieee;
use ieee.std_logic_1164.all;

entity uart_tx is
  Generic (
    BIT_DURATION : integer := 5
    );
  port ( clk   : in  std_logic;
         rst   : in  std_logic;
         data  : in  std_logic_vector (7 downto 0);
         empty : in  std_logic;
         rd_en : out std_logic;
         TX    : out std_logic
         );
end uart_tx;

architecture Behavioral of uart_tx is

  type typestate is (reposo, sampledata, b_start, B_0, B_1, B_2, B_3, B_4, B_5, B_6, B_7, B_paridad, B_stop);
  signal state, n_state: typestate;

  signal cont, p_cont: integer range 0 to BIT_DURATION-1;
  signal datai, p_datai: std_logic_vector (7 downto 0);

begin

  sinc: process(clk, rst)
  begin
    if(rst='1')then
      state<=reposo;
      cont<=0;
      datai<=(others=>'0');
    elsif(clk='1' and clk'event) then
      state<=n_state;
      cont<=p_cont;
      datai<=p_datai;
    end if;
  end process;

  comb: process(state, cont, data, datai, empty)
  begin
    n_state<=state;
    p_cont<=cont;
    p_datai<=datai;
    rd_en <= '0';
    case state is
      when reposo=>
        TX<='1';
        p_cont <= 0;
        if(empty='0')then
          rd_en <= '1';
          n_state<=sampledata;
        end if;
      when sampledata=>
        TX<='1';
        p_datai<=data;
        n_state<=b_start;
        p_cont<= 0;
      when b_start=>
        TX<='0';
        if(cont=BIT_DURATION-1)then
          p_cont<= 0;
          n_state<=b_0;
        else
          p_cont<=cont+1;
        end if;
      when b_0=>
        TX<=datai(0);
        if(cont=BIT_DURATION-1)then
          p_cont<= 0;
          n_state<=b_1;
        else
          p_cont<=cont+1;
        end if;
      when b_1=>
        TX<=datai(1);
        if(cont=BIT_DURATION-1)then
          p_cont<= 0;
          n_state<=b_2;
        else
          p_cont<=cont+1;
        end if;
      when b_2=>
        TX<=datai(2);
        if(cont=BIT_DURATION-1)then
          p_cont<= 0;
          n_state<=b_3;
        else
          p_cont<=cont+1;
        end if;
      when b_3=>
        TX<=datai(3);
        if(cont=BIT_DURATION-1)then
          p_cont<= 0;
          n_state<=b_4;
        else
          p_cont<=cont+1;
        end if;
      when b_4=>
        TX<=datai(4);
        if(cont=BIT_DURATION-1)then
          p_cont<= 0;
          n_state<=b_5;
        else
          p_cont<=cont+1;
        end if;
      when b_5=>
        TX<=datai(5);
        if(cont=BIT_DURATION-1)then
          p_cont<= 0;
          n_state<=b_6;
        else
          p_cont<=cont+1;
        end if;
      when b_6=>
        TX<=datai(6);
        if(cont=BIT_DURATION-1)then
          p_cont<=0;
          n_state<=b_7;
        else
          p_cont<=cont+1;
        end if;
      when b_7=>
        TX<=datai(7);
        if(cont=BIT_DURATION-1)then
          p_cont<=0;
          n_state<=b_paridad;
        else
          p_cont<=cont+1;
        end if;
      when b_paridad=>
        TX<=datai(0) xor datai(1) xor datai(2) xor datai(3) xor datai(4) xor datai(5) xor datai(6) xor datai(7);
        if(cont=BIT_DURATION-1)then
          p_cont<=0;
          n_state<=b_stop;
        else
          p_cont<=cont+1;
        end if;
      when b_stop=>
        TX<='1';
        if(cont=BIT_DURATION-1)then
          p_cont<=0;
          n_state<= reposo;
        else
          p_cont<=cont+1;
        end if;
    end case;
  end process;

end Behavioral;

