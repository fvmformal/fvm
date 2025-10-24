module counter #(
    parameter int MAX_COUNT = 128
) (
    input  logic        clk,
    input  logic        rst,
    output logic [7:0]  Q
);

    logic [7:0] count;
    logic [7:0] p_count;

    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            count <= 8'd0;
        else
            count <= p_count;
    end

    always_comb begin
        if (count == MAX_COUNT)
            p_count = 8'd0;
        else
            p_count = count + 1;
    end

    assign Q = count;

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
