module core (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        irq_i,
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

    wire        is_ecall;
    wire        is_ebreak;
    wire        is_mret;
    wire        illegal;
    wire        csr_we;
    wire [31:0] csr_wdata;

    wire [31:0] csr_rdata;
    wire [31:0] mstatus;
    wire [31:0] mie;
    wire [31:0] mtvec;
    wire [31:0] mepc;
    wire [31:0] mcause;
    wire [31:0] mtval;

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

    csr u_csr (
        .clk             (clk),
        .rst_n           (rst_n),
        .csr_addr_i      (instr[31:20]),
        .csr_wdata_i     (csr_wdata),
        .csr_we_i        (csr_we),
        .csr_rdata_o     (csr_rdata),
        .trap_i          (trap_enter),
        .trap_cause_i    (trap_cause),
        .trap_epc_i      (trap_epc),
        .trap_val_i      (trap_val),
        .mstatus_trap_i  (mstatus_trap),
        .mret_i          (is_mret),
        .mstatus_mret_i  (mstatus_mret),
        .irq_i           (irq_i),
        .mstatus_o       (mstatus),
        .mie_o           (mie),
        .mtvec_o         (mtvec),
        .mepc_o          (mepc),
        .mcause_o        (mcause),
        .mtval_o         (mtval)
    );

    control u_control (
        .instr        (instr),
        .r1           (r1),
        .r2           (r2),
        .csr_rdata    (csr_rdata),
        .imm          (imm),
        .wreg         (wreg),
        .wreg_src     (wreg_src),
        .pc_src       (pc_src),
        .branch_taken (branch_taken),
        .alu_src_b    (alu_src_b),
        .alu_op       (alu_op),
        .mem_write    (mem_write),
        .mem_func     (mem_func),
        .is_ecall     (is_ecall),
        .is_ebreak    (is_ebreak),
        .is_mret      (is_mret),
        .illegal      (illegal),
        .csr_we       (csr_we),
        .csr_wdata    (csr_wdata)
    );

    regfile u_regfile (
        .clk    (clk),
        .rst_n  (rst_n),
        .rs1    (instr[19:15]),
        .rs2    (instr[24:20]),
        .rd     (instr[11:7]),
        .we     (wreg && !sync_trap),
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
        .we      (mem_write && !sync_trap),
        .funct3  (mem_func),
        .wdata   (r2),
        .rdata   (rdata)
    );

    assign pc_plus_4   = pc + 32'd4;
    assign pc_plus_imm = pc + imm;
    assign jalr_target = (r1 + imm) & ~32'd1;

    wire        sync_trap;
    wire        irq_pending;
    wire        trap_enter;
    wire [31:0] trap_cause;
    wire [31:0] trap_epc;
    wire [31:0] trap_val;
    wire [31:0] mstatus_trap;
    wire [31:0] mstatus_mret;

    assign sync_trap = illegal || is_ecall || is_ebreak;
    assign irq_pending = irq_i && mstatus[3] && mie[11];
    assign trap_enter = sync_trap || irq_pending;

    assign trap_cause = illegal  ? 32'd2   :
                        is_ebreak ? 32'd3   :
                        is_ecall  ? 32'd8   : 32'h8000000b;
    assign trap_epc = sync_trap ? pc : pc_plus_4;
    assign trap_val = illegal ? instr : 32'b0;

    assign mstatus_trap = (mstatus & ~32'h00000008) | ((mstatus & 32'h00000008) << 4);
    assign mstatus_mret = (mstatus & ~32'h00000008) | ((mstatus >> 4) & 32'h00000008);

    assign next_pc = trap_enter   ? {mtvec[31:2], 2'b00} :
                     is_mret      ? mepc                 :
                     (pc_src == 2'b01)  ? pc_plus_imm :
                     (pc_src == 2'b10)  ? jalr_target : pc_plus_4;

    assign wdata = (wreg_src == 3'd0) ? imm :
                   (wreg_src == 3'd1) ? pc_plus_imm :
                   (wreg_src == 3'd2) ? pc_plus_4 :
                   (wreg_src == 3'd3) ? alu_result :
                   (wreg_src == 3'd4) ? rdata :
                   (wreg_src == 3'd5) ? csr_rdata : 32'b0;

    assign pc_out = pc;

endmodule
