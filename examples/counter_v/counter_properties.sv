bind counter counter_sva sva_inst (
    .clk(clk),
    .rst(rst),
    .Q(Q)
);

module counter_sva(
    input logic        clk,
    input logic        rst,
    input logic [7:0]  Q
);

    property reset_clears_count;
        @(posedge clk)
        rst |=> (Q == 8'd0);
    endproperty
    assert property (reset_clears_count);

    property count_increments;
        @(posedge clk)
        disable iff (rst)
        (Q != 8'd128) |=> (Q == $past(Q) + 1);
    endproperty
    assert property (count_increments);

    property count_wraps;
        @(posedge clk)
        disable iff (rst)
        (Q == 8'd128) |=> (Q == 8'd0);
    endproperty
    assert property (count_wraps);

    cover property (
        @(posedge clk)
        disable iff (rst)
        (Q == 8'd128) ##1
        (Q == 8'd0)
    );

endmodule
