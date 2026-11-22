module regfile (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [4:0]  rs1,
    input  wire [4:0]  rs2,
    input  wire [4:0]  rd,
    input  wire        we,
    input  wire [31:0] wdata,
    output wire [31:0] rdata1,
    output wire [31:0] rdata2
);

    reg [31:0] regs [0:31];
    integer i;

    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1)
                regs[i] <= 32'b0;
        end else if (we && (rd != 5'd0)) begin
            regs[rd] <= wdata;
        end
    end

    // 同一拍写回的寄存器直接把写入值送到读端口，不必等下一拍
    assign rdata1 = (rs1 == 5'd0) ? 32'b0 :
                    (we && (rd == rs1)) ? wdata : regs[rs1];
    assign rdata2 = (rs2 == 5'd0) ? 32'b0 :
                    (we && (rd == rs2)) ? wdata : regs[rs2];

endmodule
