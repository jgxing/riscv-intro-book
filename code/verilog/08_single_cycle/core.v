module core (
    input  wire        clk,
    input  wire        rst_n,
    output wire [31:0] pc_out
);

    wire [31:0] pc;
    wire [31:0] next_pc;
    wire [31:0] instr;
    wire [31:0] imm;
    wire [31:0] r1;
    wire [31:0] r2;
    wire [31:0] alu_result;
    wire [31:0] wdata;
    wire [31:0] rdata;
    wire [31:0] pc_plus_4;
    wire [31:0] pc_plus_imm;
    wire [31:0] jalr_target;

    wire        wreg;
    wire [2:0]  wreg_src;
    wire [1:0]  pc_src;
    wire        branch_taken;
    wire        alu_src_b;
    wire [3:0]  alu_op;
    wire        mem_write;
    wire [2:0]  mem_func;

    pc u_pc (
        .clk     (clk),
        .rst_n   (rst_n),
        .next_pc (next_pc),
        .cur_pc  (pc)
    );

    imem u_imem (
        .addr  (pc),
        .instr (instr)
    );

    control u_control (
        .instr        (instr),
        .r1           (r1),
        .r2           (r2),
        .imm          (imm),
        .wreg         (wreg),
        .wreg_src     (wreg_src),
        .pc_src       (pc_src),
        .branch_taken (branch_taken),
        .alu_src_b    (alu_src_b),
        .alu_op       (alu_op),
        .mem_write    (mem_write),
        .mem_func     (mem_func)
    );

    regfile u_regfile (
        .clk    (clk),
        .rst_n  (rst_n),
        .rs1    (instr[19:15]),
        .rs2    (instr[24:20]),
        .rd     (instr[11:7]),
        .we     (wreg),
        .wdata  (wdata),
        .rdata1 (r1),
        .rdata2 (r2)
    );

    alu u_alu (
        .a      (r1),
        .b      (alu_src_b ? imm : r2),
        .alu_op (alu_op),
        .result (alu_result)
    );

    dmem u_dmem (
        .clk     (clk),
        .addr    (alu_result),
        .we      (mem_write),
        .funct3  (mem_func),
        .wdata   (r2),
        .rdata   (rdata)
    );

    assign pc_plus_4   = pc + 32'd4;
    assign pc_plus_imm = pc + imm;
    assign jalr_target = (r1 + imm) & ~32'd1;

    assign next_pc = (pc_src == 2'b00) ? pc_plus_4 :
                     (pc_src == 2'b01) ? pc_plus_imm :
                     (pc_src == 2'b10) ? jalr_target : pc_plus_4;

    assign wdata = (wreg_src == 3'd0) ? imm :
                   (wreg_src == 3'd1) ? pc_plus_imm :
                   (wreg_src == 3'd2) ? pc_plus_4 :
                   (wreg_src == 3'd3) ? alu_result :
                   (wreg_src == 3'd4) ? rdata : 32'b0;

    assign pc_out = pc;

endmodule
