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

    localparam [1:0] PC_PC4  = 2'd0;
    localparam [1:0] PC_IMM  = 2'd1;
    localparam [1:0] PC_JALR = 2'd2;

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
        if (!rst_n || redirect) begin
            ifid_pc    <= 32'b0;
            ifid_pc4   <= 32'b0;
            ifid_instr <= 32'b0;
        end else if (!lw_stall) begin
            ifid_pc    <= pc;
            ifid_pc4   <= pc_plus_4;
            ifid_instr <= instr_if;
        end
    end

    // ---------- ID：译码与读寄存器堆 ----------
    wire [4:0] rs1_id = ifid_instr[19:15];
    wire [4:0] rs2_id = ifid_instr[24:20];
    wire [4:0] rd_id  = ifid_instr[11:7];
    wire [6:0] op_id  = ifid_instr[6:0];
    wire [2:0] f3_id  = ifid_instr[14:12];

    wire is_jal_id    = (op_id == 7'b1101111);
    wire is_jalr_id   = (op_id == 7'b1100111);
    wire is_branch_id = (op_id == 7'b1100011);

    wire [31:0] r1_id;
    wire [31:0] r2_id;
    wire [31:0] imm_id;
    wire        wreg_id;
    wire [2:0]  wreg_src_id;
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
        .pc_src       (),
        .branch_taken (),
        .alu_src_b    (alu_src_b_id),
        .alu_op       (alu_op_id),
        .mem_write    (mem_write_id),
        .mem_func     (mem_func_id)
    );

    // WB 级回送，写寄存器堆
    wire [31:0] wb_wdata;
    wire [4:0]  wb_rd;
    wire        wb_wreg;

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

    // ---------- 冒险检测（组合逻辑） ----------
    // load-use：ID/EX 里是 load，且它的目标正好是 IF/ID 要读的源寄存器
    wire lw_stall =
        (idex_wreg_src == WR_MEM) && (idex_rd != 5'd0) &&
        ((idex_rd == rs1_id) || (idex_rd == rs2_id));

    // ---------- ID/EX 流水线寄存器 ----------
    reg [31:0] idex_pc;
    reg [31:0] idex_pc4;
    reg [31:0] idex_imm;
    reg [31:0] idex_r1;
    reg [31:0] idex_r2;
    reg [4:0]  idex_rs1;
    reg [4:0]  idex_rs2;
    reg [4:0]  idex_rd;
    reg [2:0]  idex_f3;
    reg        idex_is_jal;
    reg        idex_is_jalr;
    reg        idex_is_branch;
    reg        idex_wreg;
    reg [2:0]  idex_wreg_src;
    reg        idex_alu_src_b;
    reg [3:0]  idex_alu_op;
    reg        idex_mem_write;
    reg [2:0]  idex_mem_func;

    always @(posedge clk) begin
        if (!rst_n || redirect || lw_stall) begin
            idex_pc         <= 32'b0;
            idex_pc4        <= 32'b0;
            idex_imm        <= 32'b0;
            idex_r1         <= 32'b0;
            idex_r2         <= 32'b0;
            idex_rs1        <= 5'b0;
            idex_rs2        <= 5'b0;
            idex_rd         <= 5'b0;
            idex_f3         <= 3'b0;
            idex_is_jal     <= 1'b0;
            idex_is_jalr    <= 1'b0;
            idex_is_branch  <= 1'b0;
            idex_wreg       <= 1'b0;
            idex_wreg_src   <= 3'b0;
            idex_alu_src_b  <= 1'b0;
            idex_alu_op     <= 4'b0;
            idex_mem_write  <= 1'b0;
            idex_mem_func   <= 3'b0;
        end else begin
            idex_pc         <= ifid_pc;
            idex_pc4        <= ifid_pc4;
            idex_imm        <= imm_id;
            idex_r1         <= r1_id;
            idex_r2         <= r2_id;
            idex_rs1        <= rs1_id;
            idex_rs2        <= rs2_id;
            idex_rd         <= rd_id;
            idex_f3         <= f3_id;
            idex_is_jal     <= is_jal_id;
            idex_is_jalr    <= is_jalr_id;
            idex_is_branch  <= is_branch_id;
            idex_wreg       <= wreg_id;
            idex_wreg_src   <= wreg_src_id;
            idex_alu_src_b  <= alu_src_b_id;
            idex_alu_op     <= alu_op_id;
            idex_mem_write  <= mem_write_id;
            idex_mem_func   <= mem_func_id;
        end
    end

    // ---------- EX：转发与执行 ----------
    // EX/MEM 结果优先于 MEM/WB；load 在 EX/MEM 阶段还没有数据，排除掉
    wire exmem_hit_a = exmem_wreg && (exmem_rd != 5'd0) &&
                       (exmem_wreg_src != WR_MEM) && (exmem_rd == idex_rs1);
    wire exmem_hit_b = exmem_wreg && (exmem_rd != 5'd0) &&
                       (exmem_wreg_src != WR_MEM) && (exmem_rd == idex_rs2);
    wire memwb_hit_a = memwb_wreg && (memwb_rd != 5'd0) && (memwb_rd == idex_rs1);
    wire memwb_hit_b = memwb_wreg && (memwb_rd != 5'd0) && (memwb_rd == idex_rs2);

    wire [31:0] r1_ex = exmem_hit_a ? exmem_wdata :
                        memwb_hit_a ? memwb_wdata : idex_r1;
    wire [31:0] r2_ex = exmem_hit_b ? exmem_wdata :
                        memwb_hit_b ? memwb_wdata : idex_r2;

    wire [31:0] alu_a = r1_ex;
    wire [31:0] alu_b = idex_alu_src_b ? idex_imm : r2_ex;
    wire [31:0] alu_result_ex;

    alu u_alu (
        .a      (alu_a),
        .b      (alu_b),
        .alu_op (idex_alu_op),
        .result (alu_result_ex)
    );

    // 分支条件在 EX 级用转发后的操作数重新判断
    wire eq_ex  = (r1_ex == r2_ex);
    wire lt_ex  = ($signed(r1_ex) < $signed(r2_ex));
    wire ltu_ex = (r1_ex < r2_ex);

    reg branch_taken_ex;
    always @(*) begin
        case (idex_f3)
            3'b000: branch_taken_ex = eq_ex;
            3'b001: branch_taken_ex = !eq_ex;
            3'b100: branch_taken_ex = lt_ex;
            3'b101: branch_taken_ex = !lt_ex;
            3'b110: branch_taken_ex = ltu_ex;
            3'b111: branch_taken_ex = !ltu_ex;
            default: branch_taken_ex = 1'b0;
        endcase
    end

    wire [1:0] pc_src_ex =
        idex_is_jal                          ? PC_IMM  :
        idex_is_jalr                         ? PC_JALR :
        (idex_is_branch && branch_taken_ex)  ? PC_IMM  : PC_PC4;

    wire redirect = (pc_src_ex != PC_PC4);

    wire [31:0] jalr_target = (r1_ex + idex_imm) & ~32'h1;

    assign next_pc =
        lw_stall                      ? pc :
        (pc_src_ex == PC_IMM)         ? (idex_pc + idex_imm) :
        (pc_src_ex == PC_JALR)        ? jalr_target :
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
            exmem_r2         <= r2_ex;
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
