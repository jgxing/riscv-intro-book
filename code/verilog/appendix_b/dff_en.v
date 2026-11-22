module dff_en (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    input  wire       d,
    output reg        q
);

    always @(posedge clk) begin
        if (!rst_n)
            q <= 1'b0;
        else if (en)
            q <= d;
    end

endmodule
