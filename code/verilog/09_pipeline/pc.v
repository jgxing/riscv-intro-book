module pc (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] next_pc,
    output reg  [31:0] cur_pc
);

    localparam [31:0] RESET_PC = 32'h00400000;

    always @(posedge clk) begin
        if (!rst_n)
            cur_pc <= RESET_PC;
        else
            cur_pc <= next_pc;
    end

endmodule
