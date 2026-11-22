module core (
    input  wire        clk,
    input  wire        rst_n,
    output wire [31:0] pc_out
);

    localparam [2:0] WR_IMM   = 3'd0;
    localparam [2:0] WR_PCIMM = 3'd1;
    localparam [2:0] WR_PC4   = 3'd2;
    localparam [2:0] WR_ALU   = 3'd3;
    localparam [2:0] WR_MEM   = 3'd4;

    // WB 级产生，回送到 ID 级写寄存器堆
    wire [31:0] wb_wdata;
    wire [4:0]  wb_rd;
    wire        wb_wreg;

    // ---------- IF：取指 ----------
    wire [31:0] pc;
    wire [31:0] pc_plus_4 = pc + 32'd4;
    wire [31:0] instr_if;
    wire [31:0] next_pc;

    pc u_pc (
        .clk     (clk),
        .rst_n   (rst_n),
        .next_pc (next_pc),
        .cur_pc  (pc)
    );

    imem u_imem (
        .addr  (pc),
        .instr (instr_if)
    );

    // ---------- IF/ID 流水线寄存器 ----------
    reg [31:0] ifid_pc;
    reg [31:0] ifid_pc4;
    reg [31:0] ifid_instr;

    always @(posedge clk) begin
        if (!rst_n) begin
            ifid_pc    <= 32'b0;
            ifid_pc4   <= 32'b0;
            ifid_instr <= 32'b0;
        end else begin
            ifid_pc    <= pc;
            ifid_pc4   <= pc_plus_4;
            ifid_instr <= instr_if;
        end
    end

    // ---------- ID：译码与读寄存器堆 ----------
    wire [4:0] rs1_id = ifid_instr[19:15];
    wire [4:0] rs2_id = ifid_instr[24:20];
    wire [4:0] rd_id  = ifid_instr[11:7];

    wire [31:0] r1_id;
    wire [31:0] r2_id;
    wire [31:0] imm_id;
    wire        wreg_id;
    wire [2:0]  wreg_src_id;
    wire [1:0]  pc_src_id;
    wire        branch_taken_id;
    wire        alu_src_b_id;
    wire [3:0]  alu_op_id;
    wire        mem_write_id;
    wire [2:0]  mem_func_id;

    control u_ctrl (
        .instr        (ifid_instr),
        .r1           (r1_id),
        .r2           (r2_id),
        .imm          (imm_id),
        .wreg         (wreg_id),
        .wreg_src     (wreg_src_id),
        .pc_src       (pc_src_id),
        .branch_taken (branch_taken_id),
        .alu_src_b    (alu_src_b_id),
        .alu_op       (alu_op_id),
        .mem_write    (mem_write_id),
        .mem_func     (mem_func_id)
    );

    regfile u_regfile (
        .clk     (clk),
        .rst_n   (rst_n),
        .rs1     (rs1_id),
        .rs2     (rs2_id),
        .rd      (wb_rd),
        .we      (wb_wreg),
        .wdata   (wb_wdata),
        .rdata1  (r1_id),
        .rdata2  (r2_id)
    );

    // ---------- ID/EX 流水线寄存器 ----------
    reg [31:0] idex_pc;
    reg [31:0] idex_pc4;
    reg [31:0] idex_imm;
    reg [31:0] idex_r1;
    reg [31:0] idex_r2;
    reg [4:0]  idex_rd;
    reg        idex_wreg;
    reg [2:0]  idex_wreg_src;
    reg [1:0]  idex_pc_src;
    reg        idex_alu_src_b;
    reg [3:0]  idex_alu_op;
    reg        idex_mem_write;
    reg [2:0]  idex_mem_func;

    always @(posedge clk) begin
        if (!rst_n) begin
            idex_pc        <= 32'b0;
            idex_pc4       <= 32'b0;
            idex_imm       <= 32'b0;
            idex_r1        <= 32'b0;
            idex_r2        <= 32'b0;
            idex_rd        <= 5'b0;
            idex_wreg      <= 1'b0;
            idex_wreg_src  <= 3'b0;
            idex_pc_src    <= 2'b0;
            idex_alu_src_b <= 1'b0;
            idex_alu_op    <= 4'b0;
            idex_mem_write <= 1'b0;
            idex_mem_func  <= 3'b0;
        end else begin
            idex_pc        <= ifid_pc;
            idex_pc4       <= ifid_pc4;
            idex_imm       <= imm_id;
            idex_r1        <= r1_id;
            idex_r2        <= r2_id;
            idex_rd        <= rd_id;
            idex_wreg      <= wreg_id;
            idex_wreg_src  <= wreg_src_id;
            idex_pc_src    <= pc_src_id;
            idex_alu_src_b <= alu_src_b_id;
            idex_alu_op    <= alu_op_id;
            idex_mem_write <= mem_write_id;
            idex_mem_func  <= mem_func_id;
        end
    end

    // ---------- EX：执行 ----------
    wire [31:0] alu_a = idex_r1;
    wire [31:0] alu_b = idex_alu_src_b ? idex_imm : idex_r2;
    wire [31:0] alu_result_ex;

    alu u_alu (
        .a      (alu_a),
        .b      (alu_b),
        .alu_op (idex_alu_op),
        .result (alu_result_ex)
    );

    wire [31:0] jalr_target = (idex_r1 + idex_imm) & ~32'h1;

    assign next_pc =
        (idex_pc_src == 2'd1) ? (idex_pc + idex_imm) :
        (idex_pc_src == 2'd2) ? jalr_target :
        pc_plus_4;

    wire [31:0] ex_wdata =
        (idex_wreg_src == WR_IMM)   ? idex_imm :
        (idex_wreg_src == WR_PCIMM) ? (idex_pc + idex_imm) :
        (idex_wreg_src == WR_PC4)   ? idex_pc4 :
        alu_result_ex;

    // ---------- EX/MEM 流水线寄存器 ----------
    reg [31:0] exmem_alu;
    reg [31:0] exmem_wdata;
    reg [31:0] exmem_r2;
    reg [4:0]  exmem_rd;
    reg        exmem_wreg;
    reg [2:0]  exmem_wreg_src;
    reg        exmem_mem_write;
    reg [2:0]  exmem_mem_func;

    always @(posedge clk) begin
        if (!rst_n) begin
            exmem_alu        <= 32'b0;
            exmem_wdata      <= 32'b0;
            exmem_r2         <= 32'b0;
            exmem_rd         <= 5'b0;
            exmem_wreg       <= 1'b0;
            exmem_wreg_src   <= 3'b0;
            exmem_mem_write  <= 1'b0;
            exmem_mem_func   <= 3'b0;
        end else begin
            exmem_alu        <= alu_result_ex;
            exmem_wdata      <= ex_wdata;
            exmem_r2         <= idex_r2;
            exmem_rd         <= idex_rd;
            exmem_wreg       <= idex_wreg;
            exmem_wreg_src   <= idex_wreg_src;
            exmem_mem_write  <= idex_mem_write;
            exmem_mem_func   <= idex_mem_func;
        end
    end

    // ---------- MEM：访存 ----------
    wire [31:0] rdata_mem;

    dmem u_dmem (
        .clk    (clk),
        .addr   (exmem_alu),
        .we     (exmem_mem_write),
        .funct3 (exmem_mem_func),
        .wdata  (exmem_r2),
        .rdata  (rdata_mem)
    );

    wire [31:0] mem_wdata =
        (exmem_wreg_src == WR_MEM) ? rdata_mem : exmem_wdata;

    // ---------- MEM/WB 流水线寄存器 ----------
    reg [31:0] memwb_wdata;
    reg [4:0]  memwb_rd;
    reg        memwb_wreg;

    always @(posedge clk) begin
        if (!rst_n) begin
            memwb_wdata <= 32'b0;
            memwb_rd    <= 5'b0;
            memwb_wreg  <= 1'b0;
        end else begin
            memwb_wdata <= mem_wdata;
            memwb_rd    <= exmem_rd;
            memwb_wreg  <= exmem_wreg;
        end
    end

    // ---------- WB：写回 ----------
    assign wb_wdata = memwb_wdata;
    assign wb_rd    = memwb_rd;
    assign wb_wreg  = memwb_wreg;

    assign pc_out = pc;

endmodule
