module counter #(
    parameter int MAX_COUNT = 128
) (
    input  logic        clk, rst,
    output logic [7:0]  Q
);

    always_ff @(posedge clk or posedge rst)
        if (rst)
            Q <= 0;
        else if (Q == MAX_COUNT)
            Q <= 0;
        else
            Q <= Q + 1;

    // ========================================================
    // SVA Properties
    // ========================================================

    property reset_clears_count;
        @(posedge clk)
        rst |-> (Q == 8'd0);
    endproperty
    assert property (reset_clears_count);

    property count_increments;
        @(posedge clk)
        disable iff (rst)
        (Q != MAX_COUNT) |=> (Q == $past(Q) + 1);
    endproperty
    assert property (count_increments);

    property count_wraps;
        @(posedge clk)
        disable iff (rst)
        (Q == MAX_COUNT) |=> (Q == 8'd0);
    endproperty
    assert property (count_wraps);

    cover property (
        @(posedge clk)
        disable iff (rst)
        (Q == MAX_COUNT) ##1
        (Q == 8'd0)
    );

endmodule
